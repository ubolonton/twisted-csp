# http://talks.golang.org/2013/advconc.slide#6
import csp


class Ball:
    hits = 0


def player(name, table):
    while True:
        # print name, "take"
        ball = yield csp.select(table.take())
        ball.hits += 1
        print name, ball.hits
        yield csp.wait(0.1)
        # print name, "put"
        yield csp.select(table.put(ball))


def main():
    table = csp.Channel()

    # print "create player ping"
    yield csp.go(player("ping", table))
    # print "create player pong"
    yield csp.go(player("pong", table))

    # print "start game"
    yield table.put(Ball())
    # print "let them play for 1 second"
    yield csp.wait(1)
    # print "stopped"
