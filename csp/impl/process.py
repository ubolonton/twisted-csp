from collections import namedtuple

from csp.impl import dispatch
from csp.impl.channels import put_then_callback, take_then_callback
from csp.impl.select import do_alts

Instruction = namedtuple("Instruction", ["op", "data"])

AltData = namedtuple("AltData", ["operations", "priority", "default"])


# XXX
NONE = object()

# TODO: If a Deferred is yielded it should be resolved instead of just
# bounced back
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

        if isinstance(instruction, Instruction):
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
            if instruction.op == "sleep":
                seconds = instruction.data
                callback = lambda: self._continue(None)
                dispatch.queue_delay(callback, seconds)
                return

            if instruction.op == "alts":
                data = instruction.data
                operations = data.operations
                do_alts(operations, self._continue, priority=data.priority, default=data.default)
                return
        else:
            self._continue(instruction)


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


def sleep(seconds):
    """Pauses the current go function.

    Must be used with "yield" inside a go function.

    # "Sleeps" for 0.5 seconds (but does not tie up the thread)
    yield sleep(0.5)
    """
    return Instruction("sleep", seconds)


# TODO: Re-organize code


def alts(operations, priority=False, default=None):
    """Completes at most one of the specified channel operations. Each
    operation must either be a channel to take from, or a tuple of
    (channel-to-put-onto, value-to-put).

    If more than 1 operation is ready, a non-deterministic choice will
    be made.

    Must be used with "yield" inside a go function.

    value = yield alts([channel, ()])
    """
    return Instruction("alts", AltData(operations, priority, default))


# TODO: Better doc
def stop(value=None):
    """Returns from the current go function with the supplied value.

    It's dual to the "return" keyword in normal functions.

    def proc(early):
        yield sleep(0.5)
        if early:
            yield stop("early")

        yield stop("late")

    # Will have "early" put on it
    chan1 = go_channel(proc, True)
    # Will have "late" put on it
    chan2 = go_channel(proc, False)
    """
    return Instruction("stop", value)
