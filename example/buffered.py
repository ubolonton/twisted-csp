import csp


def main():
    chan = csp.Channel(csp.impl.buffers.FixedBuffer(2))
    yield csp.put(chan, "buffered")
    yield csp.put(chan, "channel")
    print (yield csp.take(chan))
    print (yield csp.take(chan))
