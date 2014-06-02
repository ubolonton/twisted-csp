from twisted.trial.unittest import TestCase
from twisted.internet.defer import Deferred

from csp import Channel, put, take, alts, go, sleep, stop
from csp import put_then_callback, take_then_callback
from csp import DEFAULT
from csp import process_deferred as async

from csp.impl.operations import onto, from_coll, reduce, into, pipe

class Operations(TestCase):
    @async
    def test_from_coll(self):
        nums = range(10)
        ch = from_coll(nums)
        for num in nums:
            self.assertEqual(num, (yield take(ch)))
        self.assertEqual(True, ch.is_closed())

    @async
    def test_into(self):
        coll = ["a", "b", "c"]
        nums = range(10)
        ch = from_coll(nums)
        self.assertEqual(coll + nums, (yield take(into(coll, ch))))

    @async
    def test_onto(self):
        nums = range(10)
        ch = Channel()
        onto(ch, nums)
        self.assertEqual(nums, (yield take(into([], ch))))

    @async
    def test_reduce(self):
        nums = range(10)
        src = from_coll(nums)
        dst = reduce(lambda x, y: x + y, 0, src)
        self.assertEqual(sum(nums), (yield take(dst)))

    @async
    def test_pipe(self):
        nums = range(10)
        dst = Channel()
        src = from_coll(nums)
        pipe(src, dst)
        self.assertEqual(nums, (yield take(into([], dst))))
