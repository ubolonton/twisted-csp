import csp

def go():
    chan = csp.Channel(2)

    @csp.process
    def run():
        yield chan.put("buffered")
        yield chan.put("channel")

        print (yield chan.take())
        print (yield chan.take())

    run()

csp.test(go)
