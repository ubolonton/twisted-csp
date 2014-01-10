from zope.interface import implements

from collections import namedtuple

# XXX: No, this should not depend on dispatcher, make a delay channel
# or sth
from csp import dispatch as dispatch
from csp.interfaces import IHandler
from csp.select import do_alts

Instruction = namedtuple("Instruction", ["op", "data"])

# PutData = namedtuple("PutData", ["channel", "value"])


# FIX: This is not efficient, right? Python has no "reify"
class FnHandler:
    implements(IHandler)

    def __init__(self, f):
        self.f = f

    def is_active(self):
        return True

    def commit(self):
        return self.f

# XXX
NONE = object()

class Process:
    def __init__(self, gen):
        self.gen = gen
        self.finished = False

    def _continue(self, response):
        # print self, "got", response
        self.run(response)

    def run(self, response = NONE):
        if self.finished:
            return

        try:
            # print self, "send", response
            if response is NONE:
                instruction = self.gen.next()
            else:
                instruction = self.gen.send(response)
        except StopIteration:
            self.finished = True
            print self, "finished"
            # FIX XXX HACK
            onFinish = getattr(self, "onFinish", None)
            if onFinish:
               onFinish()
            return

        assert isinstance(instruction, Instruction)

        if instruction.op == "put":
            channel, value = instruction.data
            result = channel.put(value, FnHandler(self._continue))
            if result:
                # print self, "immediate put", result.value
                self._continue(result.value)
            return

        if instruction.op == "take":
            channel = instruction.data
            result = channel.take(FnHandler(self._continue))
            if result:
                # print self, "immediate take", result.value
                self._continue(result.value)
            return

        if instruction.op == "wait":
            seconds = instruction.data
            dispatch.queue_delay((lambda: self._continue(None)), seconds)
            return

        if instruction.op == "alts":
            operations = instruction.data
            result = do_alts(operations, self._continue)
            if result:
                self._continue(result.value)
            return


def put(channel, value):
    return Instruction("put", (channel, value))


def take(channel):
    return Instruction("take", channel)


def wait(seconds):
    return Instruction("wait", seconds)


# TODO: Re-organize code
def alts(operations):
    return Instruction("alts", operations)
