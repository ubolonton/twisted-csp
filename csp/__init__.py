# API
from csp.impl.buffers import FixedBuffer, DroppingBuffer, SlidingBuffer
from csp.impl.channels import ManyToManyChannel as Channel
from csp.impl.process import put, take, wait, alts, stop
from csp.impl.timers import timeout

import csp.impl.process


def go(gen):
    channel = Channel(FixedBuffer(1))
    def done(value):
        if value is not None:
            channel.put(value, csp.impl.process.FnHandler(lambda: None))
        channel.close()

    process = csp.impl.process.Process(gen, done)
    process.run()
    return channel


# For API consistency (sort of)
def close(channel):
    return channel.close()
