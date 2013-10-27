import csp


chan = csp.Channel(2)


def main():
    yield chan.put("buffered")
    yield chan.put("channel")
    print (yield chan.take())
    print (yield chan.take())
