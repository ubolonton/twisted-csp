from twisted.trial.unittest import TestCase
from twisted.internet.defer import Deferred

from csp.test_helpers import async
from csp import Channel, put, take, alts, go, sleep, stop
from csp import put_then_callback, take_then_callback


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
