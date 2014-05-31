# API
from csp.impl.buffers import FixedBuffer, DroppingBuffer, SlidingBuffer
from csp.impl.channels import ManyToManyChannel as Channel, CLOSED
from csp.impl.channels import put_then_callback, take_then_callback
from csp.impl.process import put, take, sleep, alts, stop
from csp.impl.timers import timeout
from csp.impl.select import DEFAULT

import csp.impl.process

from twisted.internet.defer import Deferred


def go(f, *args, **kwargs):
    process = csp.impl.process.Process(f(*args, **kwargs))
    process.run()


def go_channel(f, *args, **kwargs):
    channel = Channel(1)
    def done(value):
        if value == CLOSED:
            channel.close()
        else:
            # TODO: Clearly define and test the differences of
            # this vs. signaling closing right away (not after the
            # put is done)
            put_then_callback(channel, value, lambda ok: channel.close())
    process = csp.impl.process.Process(f(*args, **kwargs), done)
    process.run()
    return channel


def go_deferred(f, *args, **kwargs):
    d = Deferred()
    process = csp.impl.process.Process(f(*args, **kwargs), d.callback)
    process.run()
    return d


def process_channel(f):
    def returning_channel(*args, **kwargs):
        return go_channel(f, *args, **kwargs)
    return returning_channel


def process_deferred(f):
    def returning_deferred(*args, **kwargs):
        return go_deferred(f, *args, **kwargs)
    return returning_deferred


def process(f):
    def returning(*args, **kwargs):
        return go(f, *args, **kwargs)
    return returning


# For API consistency (sort of)
def close(channel):
    """Closes a channel.

    - Pending puts are ignored.
    - Pending takes are flushed with None.
    - Future puts succeed immediately.
    - Future takes receive immediately None.
    """
    return channel.close()
