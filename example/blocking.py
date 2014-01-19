from csp import Channel, put, take


def main():
    chan = Channel()
    print "will block"
    yield put(chan, "channel")
    # Will not get here
    print (yield take(chan))
