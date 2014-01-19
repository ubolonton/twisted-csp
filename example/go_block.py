from csp import go, wait, take, stop


def lazy_echo(x):
    yield wait(0.1)
    print "I'm done"
    yield stop(x)


def main():
    chan = go(lazy_echo(1))
    print (yield take(chan))

    chan = go(lazy_echo(2))
    yield wait(1)
    print (yield take(chan))

    yield stop("Done")
