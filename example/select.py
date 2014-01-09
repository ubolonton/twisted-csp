import csp


def produce(chan, value):
    yield csp.wait(0.1)
    yield csp.put(chan, value)


def main():
    chans = []
    for i in range(10):
        chan = csp.Channel()
        csp.go(produce(chan, i))
        chans.append(chan)

    yield csp.wait(0.3)

    while True:
        value, chan = yield csp.alts(chans)
        print value
