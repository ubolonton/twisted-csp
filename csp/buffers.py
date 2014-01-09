from zope.interface import implements
from collections import deque

from csp.interfaces import IBuffer

# TODO: Check the performance charateristics

class RingBuffer:

    def __init__(self, size, iterable=()):
        self.ring = deque(iterable, size)

    def pop(self):
        return self.ring.popleft()

    def unshift(self, item):
        self.ring.append(item)

    def unbounded_unshift(self, item):
        if self.is_full():
            self.resize()
        self.unshift(item)

    def resize(self):
        self.ring = deque(self.ring, self.ring.maxlen * 2)

    def cleanup(self, keep):
        i, n = 0, len(self.ring)
        while True:
            i += 1
            if i > n:
                break
            item = self.ring.popleft()
            if keep(item):
                self.ring.append(item)

    def is_full(self):
        return len(self.ring) == self.ring.maxlen

    def __len__(self):
        return len(self.ring)

    def __repr__(self):
        return "<RingBuffer %s>" % self.ring.__repr__()


# TODO FIX: Do we really need to wrap RingBuffer like this?
class FixedBuffer:
    implements(IBuffer)

    def __init__(self, size):
        assert size > 0
        self.buf = RingBuffer(size)

    def is_full(self):
        return self.buf.is_full()

    def add(self, item):
        assert not self.is_full()
        return self.buf.unshift(item)

    def remove(self):
        return self.buf.pop()

    def __len__(self):
        return len(self.buf)


# TODO
class DroppingBuffer:
    implements(IBuffer)


# TODO
class SlidingBuffer:
    implements(IBuffer)
