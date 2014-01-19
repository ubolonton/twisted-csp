# http://talks.golang.org/2012/concurrency.slide#34
# Fan-in using select

import csp

from .boring import boring

def fan_in(input1, input2):
    c = csp.Channel()
    def collect():
        while True:
            value, _ = yield csp.alts([input1, input2])
            yield csp.put(c, value)
    csp.go(collect())
    return c


def main():
    c = fan_in(boring("Joe"), boring("Ann"))
    for i in range(10):
        print (yield csp.take(c))
    print "You are boring; I'm leaving."
