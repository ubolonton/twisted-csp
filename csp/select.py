from zope.interface import implements
from collections import namedtuple
from random import shuffle

from csp.interfaces import IHandler
from csp.channels import Box

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
def do_alts(operations, handler):
    # XXX Hmm
    assert len(operations) > 0
    flag = [True]
    operations = list(operations)
    # TODO: Accept a priority function or something
    shuffle(operations)

    for operation in operations:
        if isinstance(operation, (list, tuple)):
            port, value = operation
            result = port.put(value, AltHandler(flag, lambda: handler(AltResult(None, port))))
        else:
            port = operation
            result = port.take(AltHandler(flag, lambda value: handler(AltResult(value, port))))
        if result:
            assert isinstance(result, Box)
            return Box(AltResult(result.value, port))

    # return None
