import csp


def main():
    chan = csp.Channel(2)
    yield chan.put("buffered")
    yield chan.put("channel")
    print (yield chan.take())
    print (yield chan.take())
