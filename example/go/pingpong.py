# http://talks.golang.org/2013/advconc.slide#6
import csp


class Ball:
    hits = 0


def player(name, table):
    while True:
        ball = yield csp.take(table)
        ball.hits += 1
        print name, ball.hits
        yield csp.wait(0.1)
        yield csp.put(table, ball)


def main():
    table = csp.Channel()

    csp.go(player("ping", table))
    csp.go(player("pong", table))

    yield csp.put(table, Ball())
    yield csp.wait(1)
