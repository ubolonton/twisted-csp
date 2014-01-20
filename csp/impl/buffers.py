from zope.interface import implements
from collections import deque

from csp.impl.interfaces import IBuffer

# TODO: Check the performance characteristics. A hand-rolled
# linked-list based ring buffer may be better.

class RingBuffer:

    def __init__(self, size, iterable=()):
        self.ring = deque(iterable, size)

    def pop(self):
        """Returns the oldest item, removing it from the buffer.
        """
        return self.ring.popleft()

    def unshift(self, item):
        """Adds 1 item, dropping oldest item to make place if needed.
        """
        self.ring.append(item)

    def unbounded_unshift(self, item):
        """Adds 1 item, extending the buffer to make place if needed.
        """
        if len(self.ring) == self.ring.maxlen:
            self.resize()
        self.unshift(item)

    def resize(self):
        """Doubles the size of the buffer.
        """
        self.ring = deque(self.ring, self.ring.maxlen * 2)

    def cleanup(self, keep):
        """Removes items that do not match the specified predicate.
        """
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
    """Creates a fixed buffer of given size. When full, puts will block.
    """

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
    """Creates a fixed buffer of given size. When full, puts will complete
    but value will be dropped.
    """

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
    """Creates a fixed buffer of given size. When full, puts will complete
    but the oldest values will be dropped to make place.
    """

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
