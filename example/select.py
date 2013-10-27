import csp



@csp.process
def one(chan):
    start, end = yield csp.wait(0.5)
    print end - start, start, end
    yield chan.put("one")


@csp.process
def two(chan):
    start, end = yield csp.wait(0.5)
    print end - start, start, end
    yield chan.put("two")


def q(chan):
    start, end = yield csp.wait(0.5)
    print end - start, start, end
    yield chan.put(None)


def main():
    chan1 = csp.Channel()
    chan2 = csp.Channel()
    quit = csp.Channel()

    one(chan1)
    two(chan2)
    csp.go(q(quit))

    while True:
        chan = yield csp.select(chan1, chan2, quit)
        if chan is chan1:
            print "1", (yield chan1.take())
        if chan is chan2:
            print "2", (yield chan2.take())
        if chan is quit:
            print "quit", (yield quit.take())
