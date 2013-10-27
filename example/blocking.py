import csp


chan = csp.Channel()


def main():
    print "will block"
    yield chan.put("channel")
    # Will not get here
    print (yield chan.take())
