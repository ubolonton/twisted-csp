# http://talks.golang.org/2013/advconc.slide#6
import csp


class Ball:
    hits = 0


def player(name, table):
    while True:
        ball = yield table.take()
        ball.hits += 1
        print name, ball.hits
        yield csp.wait(0.1)
        yield table.put(ball)


def main(*args):
    table = csp.Channel()

    yield csp.go(player("ping", table))
    yield csp.go(player("pong", table))

    yield table.put(Ball())
    yield csp.wait(1)
