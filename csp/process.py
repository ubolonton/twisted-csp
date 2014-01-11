from zope.interface import implements

from collections import namedtuple

from csp import dispatch as dispatch
from csp.interfaces import IHandler
from csp.select import do_alts

Instruction = namedtuple("Instruction", ["op", "data"])


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

    def __init__(self, gen, finish_callback = None):
        self.gen = gen
        self.finished = False
        self.finish_callback = finish_callback

    def _continue(self, response):
        # print self, "got", response
        # XXX: Is there be a better way to avoid infinite recursion?
        dispatch.run(lambda: self.run(response))

    # TODO: Hmm
    def _done(self, value):
        if not self.finished:
            # print self, "finished"
            self.finished = True
            if self.finish_callback:
                dispatch.run(lambda: self.finish_callback(value))

    def run(self, response = NONE):
        if self.finished:
            return

        try:
            # print self, "send", response
            if response is NONE:
                instruction = self.gen.next()
            else:
                instruction = self.gen.send(response)
        # Normal termination
        except StopIteration:
            self._done(None)
            return
        # Exceptional termination
        except:
            # TODO: Should we put the exception into the channel instead?
            self._done(None)
            raise

        assert isinstance(instruction, Instruction)

        # Early termination
        if instruction.op == "stop":
            self._done(instruction.data)
            return

        if instruction.op == "put":
            channel, value = instruction.data
            result = channel.put(value, FnHandler(self._continue))
            if result:
                # print self, "immediate put", result.value
                self._continue(result.value)
            return

        # TODO: Should we throw if the value is an exception?
        if instruction.op == "take":
            channel = instruction.data
            result = channel.take(FnHandler(self._continue))
            if result:
                # print self, "immediate take", result.value
                self._continue(result.value)
            return

        # TODO: Timeout channel instead?
        if instruction.op == "wait":
            seconds = instruction.data
            callback = lambda: self._continue(None)
            dispatch.queue_delay(callback, seconds)
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


def stop(value):
    return Instruction("stop", value)
