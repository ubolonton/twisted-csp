from csp.impl.channels import Box, ManyToManyChannel as Channel
from csp.impl.channels import put_then_callback

from csp import put, take, alts, close, stop
from csp import process, go, go_channel
from csp import CLOSED


def onto(channel, coll, keep_open=False):
    def run():
        for value in coll:
            yield put(channel, value)
        if not keep_open:
            channel.close()
    go(run)


def from_coll(coll):
    channel = Channel(len(coll))
    onto(channel, coll)
    return channel


def reduce(f, init, channel):
    def run():
        result = init
        while True:
            value = yield take(channel)
            if value == CLOSED:
                yield stop(result)
            result = f(result, value)
    return go_channel(run)


def into(coll, channel):
    result = list(coll)
    def f(result, value):
        result.append(value)
        return result
    return reduce(f, result, channel)


def pipe(src, dst, keep_open=False):
    def run():
        while True:
            value = yield take(src)
            if value == CLOSED:
                if not keep_open:
                    dst.close()
                break
            if not (yield put(dst, value)):
                break
    go(run)
    return dst
