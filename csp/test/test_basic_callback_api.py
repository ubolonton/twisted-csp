from twisted.trial.unittest import TestCase
from twisted.internet.defer import Deferred

from csp import Channel, CLOSED, DEFAULT, put_then_callback, take_then_callback

from csp import put, take, alts, go, go_channel, sleep, stop
from csp import process_deferred as async


# FIX: Duplicate tests. There should be a single test of tests against
# 2 APIs: callback-based, deferred-based


def identity_channel(x):
    ch = Channel(1)
    put_then_callback(ch, x, lambda ok: ch.close())
    return ch


class Putting(TestCase):
    @async
    def test_immediate_taken(self):
        ch = Channel()
        def taking():
            yield take(ch)
        go(taking)
        self.assertEqual((yield put(ch, 42)), True)

    @async
    def test_immediate_buffered(self):
        ch = Channel(1)
        self.assertEqual((yield put(ch, 42)), True)

    @async
    def test_immediate_closed(self):
        ch = Channel()
        ch.close()
        self.assertEqual((yield put(ch, 42)), False)

    @async
    def test_parked_taken(self):
        ch = Channel()
        def taking():
            yield sleep(0.005)
            yield take(ch)
        go(taking)
        self.assertEqual((yield put(ch, 42)), True)

    @async
    def test_parked_closed(self):
        ch = Channel()
        def closing():
            yield sleep(0.005)
            ch.close()
        go(closing)
        self.assertEqual((yield put(ch, 42)), False)

    # http://onbeyondlambda.blogspot.com/2014/04/asynchronous-naivete.html
    def test_parked_buffered(self):
        d = Deferred()
        ch = Channel(1)
        var = {"count": 0}
        def inc(ok):
            var["count"] += 1
        put_then_callback(ch, 42, inc)
        put_then_callback(ch, 42, inc)
        def taken(value):
            def checking():
                # yield control so that the second put can proceed
                yield None
                self.assertEqual(var["count"], 2, "second (buffered) put succeeds")
                d.callback(CLOSED)
            go(checking)
        take_then_callback(ch, taken)
        return d


class Taking(TestCase):
    @async
    def test_immediate_put(self):
        ch = Channel()
        def putting():
            yield put(ch, 42)
        go(putting)
        self.assertEqual((yield take(ch)), 42)

    @async
    def test_immediate_buffered(self):
        ch = Channel(1)
        yield put(ch, 42)
        self.assertEqual((yield take(ch)), 42)

    @async
    def test_immediate_closed(self):
        ch = Channel()
        ch.close()
        self.assertEqual((yield take(ch)), CLOSED)

    @async
    def test_parked_put(self):
        ch = Channel()
        def putting():
            yield sleep(0.005)
            yield put(ch, 42)
        go(putting)
        self.assertEqual((yield take(ch)), 42)

    @async
    def test_parked_closed(self):
        ch = Channel()
        def closing():
            yield sleep(0.005)
            ch.close()
        go(closing)
        self.assertEqual((yield take(ch)), CLOSED)


class Selecting(TestCase):
    @async
    def test_identity(self):
        ch = identity_channel(42)
        r = yield alts([ch])
        self.assertEqual(r.value, 42)
        self.assertEqual(r.channel, ch)

    @async
    def test_default_value(self):
        ch = Channel(1)
        r = yield alts([ch], default=42)
        self.assertEqual(r.value, 42)
        self.assertEqual(r.channel, DEFAULT)
        yield put(ch, 53)
        r = yield alts([ch], default=42)
        self.assertEqual(r.value, 53)
        self.assertEqual(r.channel, ch)

    @async
    def test_priority(self):
        nums = range(50)
        chs = [Channel(1) for _ in nums]
        for i in nums:
            yield put(chs[i], i)
        values = []
        for _ in nums:
            values.append((yield alts(chs, priority=True)).value)
        self.assertEqual(values, nums)

    # TODO: This test is non-deterministic. Use random.seed maybe?
    @async
    def test_no_priority(self):
        nums = range(50)
        chs = [Channel(1) for _ in nums]
        for i in nums:
            yield put(chs[i], i)
        values = []
        for _ in nums:
            values.append((yield alts(chs)).value)
        self.assertNotEqual(values, nums)


class Goroutine(TestCase):
    @async
    def test_yielding_normal_value(self):
        values = [42, [42], (42,), {"x": 42}, None, True, False, lambda: None]
        for value in values:
            self.assertEqual((yield value), value, "yielded value is bounced back untouched")

    @async
    def test_returning_value(self):
        def ident(x):
            yield stop(x)
        ch = go_channel(ident, 42)
        self.assertEqual((yield take(ch)), 42, "returned value is delivered")
        self.assertEqual(ch.is_closed(), True, "output channel is closed")

    @async
    def test_returning_CLOSED(self):
        def ident(x):
            yield stop(x)
        ch = go_channel(ident, CLOSED)
        self.assertEqual((yield take(ch)), CLOSED, "CLOSED is delivered")
        self.assertEqual(ch.is_closed(), True, "output channel is closed")


class ProcessRunnerStack(TestCase):
    import sys
    limit = sys.getrecursionlimit()
    ch = Channel()
    ch.close()

    @async
    def test_taking_from_closed_channel(self):
        i = 0
        while i < self.limit:
            i += 1
            yield take(self.ch)

    @async
    def test_putting_onto_closed_channel(self):
        i = 0
        while i < self.limit:
            i += 1
            yield put(self.ch, 42)

    @async
    def test_selecting_on_closed_channel(self):
        i = 0
        while i < self.limit:
            i += 1
            yield alts([self.ch, [self.ch, 1]])

    @async
    def test_immediate_puts_and_takes(self):
        ch = Channel(1)
        i = 0
        while i < self.limit:
            i += 1
            yield put(ch, 1)
            yield take(ch)
