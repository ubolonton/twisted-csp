from csp import spawn, sleep, take, stop


def lazy_echo(x):
    yield sleep(0.1)
    print "I'm done"
    yield stop(x)


def main():
    chan = spawn(lazy_echo(1), chan=True)
    print (yield take(chan))

    chan = spawn(lazy_echo(2), chan=True)
    yield sleep(1)
    print (yield take(chan))

    yield stop("Done")
