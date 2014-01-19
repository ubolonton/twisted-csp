# http://talks.golang.org/2012/concurrency.slide#39
# Daisy-chain

import csp


def f(left, right):
    yield csp.put(left, 1 + (yield csp.take(right)))


def main():
    n = 1000
    leftmost = csp.Channel()
    right = leftmost
    left = leftmost
    for i in range(n):
        right = csp.Channel()
        csp.go(f(left, right))
        left = right

    def start(c):
        yield csp.put(c, 1)

    csp.go(start(right))
    print (yield csp.take(leftmost))
