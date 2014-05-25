# http://talks.golang.org/2013/advconc.slide#6

from csp import Channel, put, take, spawn, sleep


class Ball:
    hits = 0


def player(name, table):
    while True:
        ball = yield take(table)
        ball.hits += 1
        print name, ball.hits
        yield sleep(0.1)
        yield put(table, ball)


def main():
    table = Channel()

    spawn(player("ping", table))
    spawn(player("pong", table))

    yield put(table, Ball())
    yield sleep(1)
