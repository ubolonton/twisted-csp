# http://talks.golang.org/2013/advconc.slide#6

from csp import Channel, put, take, go, wait


class Ball:
    hits = 0


def player(name, table):
    while True:
        ball = yield take(table)
        ball.hits += 1
        print name, ball.hits
        yield wait(0.1)
        yield put(table, ball)


def main():
    table = Channel()

    go(player("ping", table))
    go(player("pong", table))

    yield put(table, Ball())
    yield wait(1)
