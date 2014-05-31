# Alternative deferred-based API

# TODO: If we use this module do we still need Process?

# TODO: errbacks are not actually used. Isn't that weird?

# TODO: Using this, the operations are scheduled before entering "yield"
# (before process gives up control), whereas with Process runner, the
# operations are scheduled after entering "yield" (after process gives up
# control). Which one is better?

from twisted.internet.defer import Deferred, returnValue, inlineCallbacks

from csp.impl import dispatch
from csp.impl.channels import ManyToManyChannel as Channel, CLOSED
from csp.impl.channels import take_then_callback, put_then_callback
from csp.impl.select import do_alts


def put(channel, value):
    d = Deferred()
    put_then_callback(channel, value, d.callback)
    return d


def take(channel):
    d = Deferred()
    take_then_callback(channel, d.callback)
    return d


def alts(operations, priority=False, default=None):
    d = Deferred()
    do_alts(operations, d.callback, priority=priority, default=default)
    return d


def sleep(seconds):
    d = Deferred()
    dispatch.queue_delay(lambda: d.callback(None), seconds)
    return d


def stop(value=None):
    returnValue(value)


def go_channel(f, *args, **kwargs):
    f1 = inlineCallbacks(f)
    d = f1(*args, **kwargs)
    channel = Channel(1)
    def done(value):
        if value == CLOSED:
            channel.close()
        else:
            put_then_callback(channel, value, lambda ok: channel.close())
    d.addCallback(done)
    return channel


def go_deferred(f, *args, **kwargs):
    f1 = inlineCallbacks(f)
    return f1(*args, **kwargs)


go = go_deferred


# Decorators

def process_channel(f):
    def returning_channel(*args, **kwargs):
        return go_channel(f, *args, **kwargs)
    return returning_channel


process_deferred = inlineCallbacks


process = process_deferred
