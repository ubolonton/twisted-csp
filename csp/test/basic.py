from twisted.trial.unittest import TestCase

from csp.test_helpers import async
from csp import Channel, put, take, go, wait

class Putting(TestCase):
    @async
    def test_immediate_taken(self):
        ch = Channel()
        def taking():
            yield take(ch)
        go(taking())
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
            yield wait(0.005)
            yield take(ch)
        go(taking())
        self.assertEqual((yield put(ch, 42)), True)
