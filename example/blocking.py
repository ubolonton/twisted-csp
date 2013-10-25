import csp

chan = csp.Channel()

@csp.process
def run():
    print "will block"
    yield chan.put("channel")
    print (yield chan.take())

run()
