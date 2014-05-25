# http://talks.golang.org/2012/concurrency.slide#25
# Generator: function that returns a channel

from csp import Channel, put, take, go, sleep
import random


def boring(message):
    c = Channel()
    def _do():
        i = 0
        while True:
            yield put(c, "%s %d" % (message, i))
            yield sleep(random.random())
            i += 1
    go(_do)
    return c


def main():
    b = boring("boring!")
    for i in range(5):
        print "You say: \"%s\"" % (yield take(b))
    print "You are boring; I'm leaving."
