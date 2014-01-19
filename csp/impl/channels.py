from zope.interface import implements
from collections import namedtuple

from csp.impl import dispatch
from csp.impl.interfaces import IChannel
from csp.impl.buffers import RingBuffer, FixedBuffer


MAX_DIRTY = 64
MAX_QUEUE_SIZE = 1024

PutBox = namedtuple("PutBox", ["handler", "value"])

Box = namedtuple("Box", ["value"])

# TODO: 2 buffers can be replaced with 1 buffer + 1 flag: pending
# takes/puts. Should we do that?


class ManyToManyChannel:
    implements(IChannel)

    def __init__(self, buf_or_n = None):
        if buf_or_n == 0:
            buf_or_n = None
        if isinstance(buf_or_n, int):
            self.buf = FixedBuffer(buf_or_n)
        else:
            self.buf = buf_or_n

        self.takes = RingBuffer(32)
        self.puts = RingBuffer(32)
        self.dirty_takes = 0
        self.dirty_puts = 0
        self.closed = False

    def put(self, value, handler):
        if value is None:
            raise Exception("Cannot put None on a channel.")

        if self.closed or not handler.is_active():
            return Box(None)

        while True:
            try:
                taker = self.takes.pop()
            except IndexError:
                taker = None
            # There's a putter in line
            if taker is not None:
                # And he's still interested
                if taker.is_active():
                    # Confirm with both sides and give it to him
                    callback, _ = taker.commit(), handler.commit()
                    # FIX
                    dispatch.run(lambda: callback(value))
                    return Box(None)
                else:
                    continue

            # No taker
            else:
                # Confirm with putter, and put it on wait
                if self.buf is not None and not self.buf.is_full():
                    handler.commit()
                    self.buf.add(value)
                    return Box(None)
                # No more room for waiting
                else:
                    # But maybe some putters are no longer interested.
                    # Remove them...
                    if self.dirty_puts > MAX_DIRTY:
                        # Sort of garbage collection
                        self.puts.cleanup(keep = lambda putter: putter.handler.is_active())
                        self.dirty_puts = 0
                    else:
                        self.dirty_puts += 1

                    if len(self.puts) >= MAX_QUEUE_SIZE:
                        raise Exception("No more than %d pending puts are allowed on a single channel." % MAX_QUEUE_SIZE)

                    # Get the putter in line
                    self.puts.unbounded_unshift(PutBox(handler, value))
            break

    def take(self, handler):
        if not handler.is_active():
            return

        if self.buf is not None and len(self.buf) > 0:
            handler.commit()
            return Box(self.buf.remove())
        else:
            while True:
                try:
                    putter = self.puts.pop()
                except IndexError:
                    putter = None
                if putter is not None:
                    put_handler = putter.handler
                    if put_handler.is_active():
                        callback, _ = put_handler.commit(), handler.commit()
                        # XXX Why don't we just pass no param???
                        dispatch.run(lambda: callback())
                        return Box(putter.value)
                    else:
                        continue
                else:
                    if self.closed:
                        handler.commit()
                        return Box(None)
                    else:
                        if self.dirty_takes > MAX_DIRTY:
                            self.takes.cleanup(keep = lambda handler: handler.is_active())
                            self.dirty_takes = 0
                        else:
                            self.dirty_takes += 1

                        if len(self.takes) >= MAX_QUEUE_SIZE:
                            raise Exception("No more than %d pending takes are allowed on a single channel." % MAX_QUEUE_SIZE)

                        self.takes.unbounded_unshift(handler)
                break

    def close(self):
        if self.closed:
            return

        # The current semantics is that a "close" is forceful, which
        # means any pending puts or buffered values will be ignored.
        # Is that actually a good thing? Ignoring buffered values
        # sounds ok, but no response to pending puts?

        self.closed = True
        while True:
            try:
                taker = self.takes.pop()
            except IndexError:
                # TODO: Why not just continue?
                taker = None
            if taker is not None:
                if taker.is_active():
                    callback = taker.commit()
                    dispatch.run(lambda: callback(None))
            else:
                break
