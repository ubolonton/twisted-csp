# API
from csp.impl.buffers import FixedBuffer, DroppingBuffer, SlidingBuffer
from csp.impl.channels import ManyToManyChannel as Channel
from csp.impl.process import put_then_callback, take_then_callback
from csp.impl.process import put, take, wait, alts, stop
from csp.impl.timers import timeout

import csp.impl.process


def go(gen):
    channel = Channel(1)
    def done(value):
        if value is not None:
            put_then_callback(channel, value, lambda _: None)
        channel.close()

    process = csp.impl.process.Process(gen, done)
    process.run()
    return channel


# For API consistency (sort of)
def close(channel):
    return channel.close()
