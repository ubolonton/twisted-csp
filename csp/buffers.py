from zope.interface import implements
from collections import deque

from csp.interfaces import IBuffer

# TODO: Check the performance characteristics

class RingBuffer:

    def __init__(self, size, iterable=()):
        self.ring = deque(iterable, size)

    def pop(self):
        return self.ring.popleft()

    def unshift(self, item):
        self.ring.append(item)

    def unbounded_unshift(self, item):
        if len(self.ring) == self.ring.maxlen:
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

    def __len__(self):
        return len(self.ring)

    def __repr__(self):
        return "<RingBuffer %s>" % self.ring.__repr__()


class FixedBuffer:
    implements(IBuffer)

    def __init__(self, size):
        assert size > 0
        self.buf = deque((), size)

    def is_full(self):
        return len(self.buf) == self.buf.maxlen

    def add(self, item):
        assert not self.is_full()
        return self.buf.append(item)

    def remove(self):
        return self.buf.popleft()

    def __len__(self):
        return len(self.buf)

    def __repr__(self):
        return "<FixedBuffer %s>" % self.buf.__repr__()


class DroppingBuffer:
    implements(IBuffer)

    def __init__(self, size):
        assert size > 0
        self.buf = deque((), size)

    def is_full(self):
        return False

    def add(self, item):
        if len(self.buf) < self.buf.maxlen:
            return self.buf.append(item)

    def remove(self):
        return self.buf.popleft()

    def __len__(self):
        return len(self.buf)

    def __repr__(self):
        return "<DroppingBuffer %s>" % self.buf.__repr__()


class SlidingBuffer:
    implements(IBuffer)

    def __init__(self, size):
        assert size > 0
        self.buf = deque((), size)

    def is_full(self):
        return False

    def add(self, item):
        return self.buf.append(item)

    def remove(self):
        return self.buf.popleft()

    def __len__(self):
        return len(self.buf)

    def __repr__(self):
        return "<SlidingBuffer %s>" % self.buf.__repr__()
