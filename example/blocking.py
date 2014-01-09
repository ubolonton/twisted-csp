import csp


def main():
    chan = csp.Channel()
    print "will block"
    yield csp.put(chan, "channel")
    # Will not get here
    print (yield csp.take(chan))
