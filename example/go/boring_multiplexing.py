# http://talks.golang.org/2012/concurrency.slide#27
# Multiplexing

from csp import Channel, put, take, go

from .boring import boring


def fan_in(input1, input2):
    c = Channel()
    def collect(i):
        while True:
            yield put(c, (yield take(i)))
    go(collect, input1)
    go(collect, input2)
    return c


def main():
    c = fan_in(boring("Joe"), boring("Ann"))
    for i in range(10):
        print (yield take(c))
    print "You are boring; I'm leaving."
