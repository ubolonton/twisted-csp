from unittest import TestCase

from csp.impl import buffers


class FixedBuffer(TestCase):
    def test_fixed_buffer(self):
        b = buffers.FixedBuffer(2)
        self.assertEqual(len(b), 0)

        b.add(1)
        self.assertEqual(len(b), 1)

        b.add(2)
        self.assertEqual(len(b), 2)
        self.assertEqual(b.is_full(), True)

        self.assertRaises(AssertionError, lambda: b.add(3))

        self.assertEqual(b.remove(), 1)
        self.assertEqual(b.is_full(), False)
        self.assertEqual(len(b), 1)

        self.assertEqual(b.remove(), 2)
        self.assertEqual(len(b), 0)

        self.assertRaises(IndexError, lambda: b.remove())


class DroppingBuffer(TestCase):
    def test_dropping_buffer(self):
        b = buffers.DroppingBuffer(2)
        self.assertEqual(len(b), 0)

        b.add(1)
        self.assertEqual(len(b), 1)

        b.add(2)
        self.assertEqual(len(b), 2)
        self.assertEqual(b.is_full(), False)
        b.add(3)
        self.assertEqual(len(b), 2)

        self.assertEqual(b.remove(), 1)
        self.assertEqual(b.is_full(), False)
        self.assertEqual(len(b), 1)

        self.assertEqual(b.remove(), 2)
        self.assertEqual(len(b), 0)

        self.assertRaises(IndexError, lambda: b.remove())


class SlidingBuffer(TestCase):
    def test_sliding_buffer(self):
        b = buffers.SlidingBuffer(2)
        self.assertEqual(len(b), 0)

        b.add(1)
        self.assertEqual(len(b), 1)

        b.add(2)
        self.assertEqual(len(b), 2)
        self.assertEqual(b.is_full(), False)
        b.add(3)
        self.assertEqual(len(b), 2)

        self.assertEqual(b.remove(), 2)
        self.assertEqual(b.is_full(), False)
        self.assertEqual(len(b), 1)

        self.assertEqual(b.remove(), 3)
        self.assertEqual(len(b), 0)

        self.assertRaises(IndexError, lambda: b.remove())
