from collections import namedtuple

from zope.interface import implements

from csp.interfaces import IHandler
# XXX: No, this should not depend on dispatcher, make a delay channel
# or sth
import csp.dispatch as dispatch

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

    def _continue(self, response):
        # print response
        self.run(response)

    def run(self, response = NONE):
        try:
            if response is NONE:
                instruction = self.gen.next()
            else:
                instruction = self.gen.send(response)
        except StopIteration:
            print self, "finished"
            return

        if not isinstance(instruction, Instruction):
            self._continue(None)
            return

        if instruction.op == "put":
            channel, value = instruction.data
            result = channel.put(value, FnHandler(self._continue))
            if result:
                self._continue(result.value)
            return

        if instruction.op == "take":
            channel = instruction.data
            result = channel.take(FnHandler(self._continue))
            if result:
                self._continue(result.value)
            return

        if instruction.op == "wait":
            seconds = instruction.data
            dispatch.queue_delay((lambda: self._continue(None)), seconds)
            return

        if instruction.op == "wait":
            seconds = instruction.data
            dispatch.queue_delay((lambda: self._continue(None)), seconds)
            return


def put(channel, value):
    return Instruction("put", (channel, value))


def take(channel):
    return Instruction("take", channel)


def wait(seconds):
    return Instruction("wait", seconds)
