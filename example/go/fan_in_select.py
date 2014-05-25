# http://talks.golang.org/2012/concurrency.slide#34
# Fan-in using select

from csp import Channel, put, take, go, alts

from .boring import boring

def fan_in(input1, input2):
    c = Channel()
    def collect():
        while True:
            value, _ = yield alts([input1, input2])
            yield put(c, value)
    go(collect)
    return c


def main():
    c = fan_in(boring("Joe"), boring("Ann"))
    for i in range(10):
        print (yield take(c))
    print "You are boring; I'm leaving."
