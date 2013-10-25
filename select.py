import csp

def go():
    chan1 = csp.Channel()
    chan2 = csp.Channel()
    quit = csp.Channel()

    @csp.process
    def one():
        yield csp.wait(0.5)
        yield chan1.put("one")

    @csp.process
    def two():
        yield csp.wait(0.5)
        yield chan2.put("two")

    @csp.process
    def q():
        yield csp.wait(0.5)
        yield quit.put(None)

    @csp.process
    def collector():
        while True:
            chan = yield csp.select(chan1, chan2, quit)
            if chan is chan1:
                print "1", (yield chan1.take())
            if chan is chan2:
                print "2", (yield chan2.take())
            if chan is quit:
                print "quit", (yield quit.take())

    for process in (one, two, q, collector):
        process()

csp.test(go)
