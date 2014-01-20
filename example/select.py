from csp import Channel, put, take, go, alts, wait


def produce(chan, value):
    yield wait(0.1)
    yield put(chan, value)


def main():
    chans = []
    for i in range(20):
        chan = Channel()
        go(produce(chan, i))
        chans.append(chan)

    def timeout(seconds):
        chan = Channel()
        def t():
            yield wait(seconds)
            chan.close()
        go(t())
        return chan

    chans.append(timeout(0.3))

    while True:
        value, chan = yield alts(chans)
        if value is None:
            print "time out"
            break
        else:
            print value
