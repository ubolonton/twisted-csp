from csp import Channel, put, go, alts, sleep, CLOSED


def produce(chan, value):
    yield sleep(0.1)
    yield put(chan, value)


def main():
    chans = []
    for i in range(20):
        chan = Channel()
        go(produce, chan, i)
        chans.append(chan)

    def timeout(seconds):
        chan = Channel()
        def t():
            yield sleep(seconds)
            chan.close()
        go(t)
        return chan

    chans.append(timeout(0.3))

    while True:
        value, chan = yield alts(chans)
        if value == CLOSED:
            print "time out"
            break
        else:
            print value
