import csp


def main():
    chan = csp.Channel()
    print "will block"
    yield chan.put("channel")
    # Will not get here
    print (yield chan.take())
