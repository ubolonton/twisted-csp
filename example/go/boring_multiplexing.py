# http://talks.golang.org/2012/concurrency.slide#27
# Multiplexing

import csp

from .boring import boring


def fan_in(input1, input2):
    c = csp.Channel()
    def collect(i):
        while True:
            yield csp.put(c, (yield csp.take(i)))
    csp.go(collect(input1))
    csp.go(collect(input2))
    return c


def main():
    c = fan_in(boring("Joe"), boring("Ann"))
    for i in range(10):
        print (yield csp.take(c))
    print "You are boring; I'm leaving."
