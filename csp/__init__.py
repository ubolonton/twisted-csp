# API
from csp.impl.buffers import FixedBuffer, DroppingBuffer, SlidingBuffer
from csp.impl.channels import ManyToManyChannel as Channel
from csp.impl.process import put_then_callback, take_then_callback
from csp.impl.process import put, take, sleep, alts, stop
from csp.impl.timers import timeout
from csp.impl.select import DEFAULT

import csp.impl.process


def no_op(*arg):
    pass


def spawn(gen, chan=False):
    """Asynchronously executes a "goroutine", which must be a generator.

    If "chan" is True, returns a channel that will receive the result
    of the goroutine when it completes.
    """
    # Only deliver the result to a channel if requested. Ideally I
    # think the choice should be a call-site optimization (whether the
    # returned channel is used). However that probably requires the
    # construct to be built-in (I believe Clojure's core.async suffers
    # from the same problem).
    if chan:
        channel = Channel(1)
        def done(value):
            if value is not None:
                put_then_callback(channel, value, no_op)
            channel.close()

        process = csp.impl.process.Process(gen, done)
        process.run()
        return channel
    else:
        process = csp.impl.process.Process(gen)
        process.run()
        return


def go(f, args=(), kwargs={}, chan=False):
    """Creates and executes a "goroutine". The supplied function must be a
    generator function.

    If "chan" is True, returns a channel that will receive the result
    of the goroutine when it completes.
    """
    return spawn(f(*args, **kwargs), chan=chan)


# For API consistency (sort of)
def close(channel):
    """Closes a channel.

    - Pending puts are ignored.
    - Pending takes are flushed with None.
    - Future puts succeed immediately.
    - Future takes receive immediately None.
    """
    return channel.close()
