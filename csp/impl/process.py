from zope.interface import implements

from collections import namedtuple

from csp.impl import dispatch
from csp.impl.interfaces import IHandler
from csp.impl.select import do_alts

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

# TODO: Shouldn't these 2 (and FnHandler) be in "channels" module?


def put_then_callback(channel, value, callback):
    """Puts a value on the channel, calling the supplied callback when
    done, passing False if the channel was closed, True otherwise.
    """
    result = channel.put(value, FnHandler(callback))
    if result:
        callback(result.value)


def take_then_callback(channel, callback):
    """Takes from the channel, calling the supplied callback with the
    received value when done.
    """
    result = channel.take(FnHandler(callback))
    if result:
        callback(result.value)


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
            put_then_callback(channel, value, self._continue)
            return

        # TODO: Should we throw if the value is an exception?
        if instruction.op == "take":
            channel = instruction.data
            take_then_callback(channel, self._continue)
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
    """Puts a value onto the channel.

    Must be used with "yield" inside a go function.

    not_closed = yield put(channel, "value")
    """
    return Instruction("put", (channel, value))


def take(channel):
    """Takes a value from the channel.

    Must be used with "yield" inside a go function.

    value = yield take(channel)
    """
    return Instruction("take", channel)


def wait(seconds):
    """Pauses the current go function.

    Must be used with "yield" inside a go function.

    # "Sleeps" for 0.5 seconds (but does not tie up the thread)
    yield wait(0.5)
    """
    return Instruction("wait", seconds)


# TODO: Re-organize code


def alts(operations):
    """Completes at most one of the specified channel operations. Each
    operation must either be a channel to take from, or a tuple of
    (channel-to-put-onto, value-to-put).

    If more than 1 operation is ready, a non-deterministic choice will
    be made.

    Must be used with "yield" inside a go function.

    value = yield alts([channel, ()])
    """
    return Instruction("alts", operations)


# TODO: Better doc
def stop(value=None):
    """Returns from the current go function with the supplied value.

    It's dual to the "return" keyword in normal functions.

    def proc(early):
        yield wait(0.5)
        if early:
            yield stop("early")

        yield stop("late")

    # Will have "early" put on it
    chan1 = go(proc(True))
    # Will have "late" put on it
    chan2 = go(proc(False))
    """
    return Instruction("stop", value)
