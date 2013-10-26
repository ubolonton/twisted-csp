import csp

chan1 = csp.Channel()
chan2 = csp.Channel()
quit = csp.Channel()

@csp.process
def one():
    start, end = yield csp.wait(0.5)
    print end - start, start, end
    yield chan1.put("one")

@csp.process
def two():
    start, end = yield csp.wait(0.5)
    print end - start, start, end
    yield chan2.put("two")

@csp.process
def q():
    start, end = yield csp.wait(0.5)
    print end - start, start, end
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
