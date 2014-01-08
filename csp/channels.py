import collections

from zope.interface import implements

from csp.interfaces import IChannel
from csp.buffers import RingBuffer

import csp.dispatch as dispatch

MAX_DIRTY = 64
MAX_QUEUE_SIZE = 1024

PutBox = collections.namedtuple("PutBox", ["handler", "value"])

Box = collections.namedtuple("Box", ["value"])


class ManyToManyChannel:
    implements(IChannel)

    def __init__(self, buf):
        self.buf = buf

        self.takes = RingBuffer(32)
        self.puts = RingBuffer(32)
        self.dirty_takes = 0
        self.dirty_puts = 0
        self.closed = False

    def put(self, value, handler):
        if value is None:
            raise Exception("Cannot put None on a channel")

        if self.closed or not handler.is_active():
            return Box(None)

        while True:
            taker = self.takes.pop()
            # There's a putter in line
            if taker is not None:
                # And he's still interested
                if taker.is_active():
                    # Confirm with both sides and give it to him
                    callback, _ = taker.commit(), handler.commit()
                    dispatch.run(callback, value)
                    return Box(None)
                else:
                    continue

            # No taker
            else:
                # Confirm with putter, and put it on wait
                if self.buf is not None and not self.buf.full:
                    handler.commit()
                    self.buf.add(value)
                    return Box(None)
                # No more room for waiting
                else:
                    # But maybe some putters are no longer interested.
                    # Remove them...
                    if self.dirty_puts > MAX_DIRTY:
                        # FIX: Putter or sth
                        self.puts.cleanup(keep = lambda putter: putter.handler.is_active())
                        self.dirty_puts = 0
                    else:
                        self.dirty_puts += 1

                    if len(self.puts) >= MAX_QUEUE_SIZE:
                        raise Exception("Max queue size reached")

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
                putter = self.puts.pop()
                if putter is not None:
                    put_handler = putter.handler
                    if put_handler.is_active():
                        callback, _ = put_handler.commit(), handler.commit()
                        dispatch.run(callback)
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
                            raise Exception("Max queue size reached")

                        self.takes.unbounded_unshift(handler)
                break

    def close(self):
        if self.closed:
            return

        self.closed = True
        while True:
            taker = self.takes.pop()
            if taker is not None:
                if taker.is_active():
                    callback = taker.commit()
                    dispatch.run(callback, None)
            else:
                break
