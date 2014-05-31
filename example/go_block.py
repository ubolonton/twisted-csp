from csp import go_chan, sleep, take, stop


def lazy_echo(x):
    yield sleep(0.1)
    print "I'm done"
    yield stop(x)


def main():
    chan = go_chan(lazy_echo, 1)
    print (yield take(chan))

    chan = go_chan(lazy_echo, 2)
    yield sleep(1)
    print (yield take(chan))

    yield stop("Done")
