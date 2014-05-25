from zope.interface import implements
from collections import namedtuple

from csp.impl import dispatch
from csp.impl.interfaces import IChannel
from csp.impl.buffers import RingBuffer, FixedBuffer


# The number of pending puts/takes between "garbage collections"
# (removing stale (no longer interested, inactive) handlers (e.g.
# unchosen alt operations))
MAX_DIRTY = 64

# Maximum pending puts/takes allowed on a single channel
MAX_QUEUE_SIZE = 1024

PutBox = namedtuple("PutBox", ["handler", "value"])

Box = namedtuple("Box", ["value"])

# TODO: 2 buffers can be replaced with 1 buffer + 1 flag: pending
# takes/puts. Should we do that?


class ManyToManyChannel:
    """Creates a channel with an optional buffer. If buf_or_n is a number,
    a fixed buffer of that size is created and used.
    """

    implements(IChannel)

    def __init__(self, buf_or_n = None):
        if buf_or_n == 0:
            buf_or_n = None
        if isinstance(buf_or_n, int):
            self.buf = FixedBuffer(buf_or_n)
        else:
            self.buf = buf_or_n

        self.closed = False
        self.takes = RingBuffer(32)
        self.puts = RingBuffer(32)
        # Counters towards next "garbage collections"
        self.dirty_takes = 0
        self.dirty_puts = 0

    def put(self, value, handler):
        if value is None:
            raise Exception("Cannot put None on a channel.")

        if self.closed or not handler.is_active():
            return Box(not self.closed)

        while True:
            try:
                taker = self.takes.pop()
            except IndexError:
                taker = None
            # There's a pending take...
            if taker is not None:
                # ... that is still interested
                if taker.is_active():
                    # Done, shake hand, here it is
                    callback, _ = taker.commit(), handler.commit()
                    # FIX
                    dispatch.run(lambda: callback(value))
                    return Box(True)
                else:
                    continue
            # No pending takes
            else:
                # Throw the value on the queue and be done with it
                if self.buf is not None and not self.buf.is_full():
                    handler.commit()
                    self.buf.add(value)
                    return Box(True)
                # No more room for waiting
                else:
                    # Periodically remove stale puts
                    if self.dirty_puts > MAX_DIRTY:
                        self.puts.cleanup(keep = lambda putter: putter.handler.is_active())
                        self.dirty_puts = 0
                    else:
                        self.dirty_puts += 1

                    # TODO: Do a last-chance "garbage collection" to
                    # be sure?
                    if len(self.puts) >= MAX_QUEUE_SIZE:
                        raise Exception("No more than %d pending puts are allowed on a single channel." % MAX_QUEUE_SIZE)

                    # Queue this put
                    self.puts.unbounded_unshift(PutBox(handler, value))
            break

    def take(self, handler):
        if not handler.is_active():
            return

        # Waiting values go first
        if self.buf is not None and len(self.buf) > 0:
            handler.commit()
            return Box(self.buf.remove())

        while True:
            try:
                putter = self.puts.pop()
            except IndexError:
                putter = None
            # There's a pending put...
            if putter is not None:
                put_handler = putter.handler
                # ... that is still interested
                if put_handler.is_active():
                    # Done, shake hand, take it
                    callback, _ = put_handler.commit(), handler.commit()
                    dispatch.run(lambda: callback(True))
                    return Box(putter.value)
                else:
                    continue
            # No pending puts
            else:
                if self.closed:
                    handler.commit()
                    return Box(None)
                else:
                    # Periodically remove stale takes
                    if self.dirty_takes > MAX_DIRTY:
                        self.takes.cleanup(keep = lambda handler: handler.is_active())
                        self.dirty_takes = 0
                    else:
                        self.dirty_takes += 1

                    # TODO: Do a last-chance "garbage collection" to
                    # be sure?
                    if len(self.takes) >= MAX_QUEUE_SIZE:
                        raise Exception("No more than %d pending takes are allowed on a single channel." % MAX_QUEUE_SIZE)

                    # Queue this take
                    self.takes.unbounded_unshift(handler)
            break

    def close(self):
        if self.closed:
            return

        self.closed = True

        # Pending takes get "channel closed"
        while True:
            try:
                taker = self.takes.pop()
            except IndexError:
                break
            if taker.is_active():
                callback = taker.commit()
                dispatch.run(lambda: callback(None))

        # Pending puts get "channel closed"
        while True:
            try:
                putter = self.puts.pop()
            except IndexError:
                break
            handler = putter.handler
            if handler.is_active():
                callback = handler.commit()
                dispatch.run(lambda: callback(False))
