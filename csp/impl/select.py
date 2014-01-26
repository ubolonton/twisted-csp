from zope.interface import implements
from collections import namedtuple
from random import shuffle

from csp.impl.interfaces import IHandler
from csp.impl.channels import Box

class AltHandler:
    implements(IHandler)

    def __init__(self, flag, f):
        self.f = f
        self.flag = flag

    def is_active(self):
        return self.flag[0]

    def commit(self):
        self.flag[0] = False
        return self.f


AltResult = namedtuple("AltResult", ["value", "channel"])


# TODO: Support options
def do_alts(operations, callback):
    # XXX Hmm
    assert len(operations) > 0
    flag = [True]
    operations = list(operations)
    # TODO: Accept a priority function or something
    shuffle(operations)

    # XXX: Python uses function-scope not block-scope. Therefore
    # "port" is mutably shared by the iterations. The "lambda port:" trick
    # is used to pass the values of "port" to "callback", instead of
    # passing the mutable reference.
    for operation in operations:
        if isinstance(operation, (list, tuple)):
            port, value = operation
            result = port.put(value, (
                lambda port: AltHandler(flag, lambda ok: callback(AltResult(ok, port)))
            )(port))
        else:
            port = operation
            result = port.take((
                lambda port: AltHandler(flag, lambda value: callback(AltResult(value, port)))
            )(port))
        if result:
            assert isinstance(result, Box)
            return Box(AltResult(result.value, port))
