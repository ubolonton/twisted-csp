import csp


def produce(chan, value):
    yield csp.wait(0.1)
    yield csp.put(chan, value)


def main():
    chans = []
    for i in range(20):
        chan = csp.Channel()
        csp.go(produce(chan, i))
        chans.append(chan)

    def timeout(seconds):
        chan = csp.Channel()
        def t():
            yield csp.wait(seconds)
            chan.close()
        csp.go(t())
        return chan

    chans.append(timeout(0.3))

    while True:
        value, chan = yield csp.alts(chans)
        if value is None:
            print "time out"
            break
        else:
            print value
