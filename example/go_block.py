import csp


def lazy_echo(x):
    yield csp.wait(0.1)
    print "I'm done"
    yield csp.stop(x)


def main():
    chan = csp.go(lazy_echo(1))
    print (yield csp.take(chan))

    chan = csp.go(lazy_echo(2))
    yield csp.wait(1)
    print (yield csp.take(chan))

    yield csp.stop("Done")
