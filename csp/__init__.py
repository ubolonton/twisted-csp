# API
from csp.impl.buffers import FixedBuffer, DroppingBuffer, SlidingBuffer
from csp.impl.channels import ManyToManyChannel as Channel
from csp.impl.process import put_then_callback, take_then_callback
from csp.impl.process import put, take, sleep, alts, stop
from csp.impl.timers import timeout

import csp.impl.process


def no_op(*arg):
    pass


def go(gen, chan=False):
    """Asynchronously executes a "go" function (a generator returned by a
    function following certain conventions, to be exact).

    Returns a channel that will receive the result of the go function
    when it completes.
    """
    # Only deliver the result to a channel if requested. Ideally I
    # think the choice should be a call-site optimization (whether the
    # return value of "go" is used). However that probably requires
    # the construct to be built-in (I believe Clojure's core.async
    # suffers from the same problem).
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


# For API consistency (sort of)
def close(channel):
    """Closes a channel.

    - Pending puts are ignored.
    - Pending takes are flushed with None.
    - Future puts succeed immediately.
    - Future takes receive immediately None.
    """
    return channel.close()
