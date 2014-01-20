from csp import Channel, put, take


def main():
    chan = Channel(2)
    yield put(chan, "buffered")
    yield put(chan, "channel")
    print (yield take(chan))
    print (yield take(chan))
