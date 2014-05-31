from twisted.trial.unittest import TestCase
from twisted.internet.defer import Deferred, inlineCallbacks

from csp.test_helpers import async
from csp import Channel, put, take, alts, go, sleep, stop
from csp import put_then_callback, take_then_callback
from csp import DEFAULT


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
                yield None
                self.assertEqual(var["count"], 2, "second (buffered) put succeeds")
                d.callback(None)
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
        self.assertEqual((yield take(ch)), None)

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
        self.assertEqual((yield take(ch)), None)


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
        ch = go(ident, args=[42], chan=True)
        self.assertEqual((yield take(ch)), 42, "returned value is delivered")
        self.assertEqual(ch.is_closed(), True, "output channel is closed")

    @async
    def test_returning_None(self):
        def ident(x):
            yield stop(x)
        ch = go(ident, args=[None], chan=True)
        self.assertEqual((yield take(ch)), None, "None is delivered")
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


from csp import defer as d


class TestDeferreds(TestCase):
    @inlineCallbacks
    def test_parked_taken(self):
        ch = Channel()
        @inlineCallbacks
        def taking():
            yield d.sleep(0.005)
            yield d.take(ch)
        taking()
        self.assertEqual((yield d.put(ch, 42)), True)

    @inlineCallbacks
    def test_parked_closed(self):
        ch = Channel()
        @inlineCallbacks
        def closing():
            yield d.sleep(0.005)
            ch.close()
        closing()
        self.assertEqual((yield d.put(ch, 42)), False)

    @inlineCallbacks
    def test_immediate_put(self):
        ch = Channel()
        @inlineCallbacks
        def putting():
            yield d.put(ch, 42)
        putting()
        self.assertEqual((yield d.take(ch)), 42)


class DeferredPutting(TestCase):
    @inlineCallbacks
    def test_immediate_taken(self):
        ch = Channel()
        @inlineCallbacks
        def taking():
            yield d.take(ch)
        taking()
        self.assertEqual((yield d.put(ch, 42)), True)

    @inlineCallbacks
    def test_immediate_buffered(self):
        ch = Channel(1)
        self.assertEqual((yield d.put(ch, 42)), True)

    @inlineCallbacks
    def test_immediate_closed(self):
        ch = Channel()
        ch.close()
        self.assertEqual((yield d.put(ch, 42)), False)

    @inlineCallbacks
    def test_parked_taken(self):
        ch = Channel()
        @inlineCallbacks
        def taking():
            yield d.sleep(0.005)
            yield d.take(ch)
        taking()
        self.assertEqual((yield d.put(ch, 42)), True)

    @inlineCallbacks
    def test_parked_closed(self):
        ch = Channel()
        @inlineCallbacks
        def closing():
            yield d.sleep(0.005)
            ch.close()
        closing()
        self.assertEqual((yield d.put(ch, 42)), False)

    def test_parked_buffered(self):
        df = Deferred()
        ch = Channel(1)
        var = {"count": 0}
        def inc(ok):
            var["count"] += 1
        d.put(ch, 42).addCallback(inc)
        d.put(ch, 42).addCallback(inc)
        def taken(value):
            def checking():
                yield d.sleep(0.005)
                self.assertEqual(var["count"], 2, "second (buffered) put succeeds")
                df.callback(None)
            d.go(checking)
        d.take(ch).addCallback(taken)
        return df


class DeferredTaking(TestCase):
    @inlineCallbacks
    def test_immediate_put(self):
        ch = Channel()
        @inlineCallbacks
        def putting():
            yield d.put(ch, 42)
        putting()
        self.assertEqual((yield d.take(ch)), 42)

    @inlineCallbacks
    def test_immediate_buffered(self):
        ch = Channel(1)
        yield d.put(ch, 42)
        self.assertEqual((yield d.take(ch)), 42)

    @inlineCallbacks
    def test_immediate_closed(self):
        ch = Channel()
        ch.close()
        self.assertEqual((yield d.take(ch)), None)

    @inlineCallbacks
    def test_parked_put(self):
        ch = Channel()
        @inlineCallbacks
        def putting():
            yield d.sleep(0.005)
            yield d.put(ch, 42)
        putting()
        self.assertEqual((yield d.take(ch)), 42)

    @inlineCallbacks
    def test_parked_closed(self):
        ch = Channel()
        @inlineCallbacks
        def closing():
            yield d.sleep(0.005)
            ch.close()
        closing()
        self.assertEqual((yield d.take(ch)), None)


class DeferredSelecting(TestCase):
    @inlineCallbacks
    def test_identity(self):
        ch = identity_channel(42)
        r = yield d.alts([ch])
        self.assertEqual(r.value, 42)
        self.assertEqual(r.channel, ch)

    @inlineCallbacks
    def test_default_value(self):
        ch = Channel(1)
        r = yield d.alts([ch], default=42)
        self.assertEqual(r.value, 42)
        self.assertEqual(r.channel, DEFAULT)
        yield d.put(ch, 53)
        r = yield d.alts([ch], default=42)
        self.assertEqual(r.value, 53)
        self.assertEqual(r.channel, ch)

    @inlineCallbacks
    def test_priority(self):
        nums = range(50)
        chs = [Channel(1) for _ in nums]
        for i in nums:
            yield d.put(chs[i], i)
        values = []
        for _ in nums:
            values.append((yield d.alts(chs, priority=True)).value)
        self.assertEqual(values, nums)
