# http://talks.golang.org/2012/concurrency.slide#39
# Daisy-chain

from csp import Channel, put, take, spawn


def f(left, right):
    yield put(left, 1 + (yield take(right)))


def main():
    n = 100000
    leftmost = Channel()
    right = leftmost
    left = leftmost
    for i in range(n):
        right = Channel()
        spawn(f(left, right))
        left = right

    def start(c):
        yield put(c, 1)

    spawn(start(right))
    print (yield take(leftmost))
