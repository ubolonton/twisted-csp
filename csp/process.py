from collections import namedtuple

from zope.interface import implements

from csp.interfaces import IHandler

Instruction = namedtuple("Instruction", ["op", "data"])

# PutData = namedtuple("PutData", ["channel", "value"])


# FIX: This is not efficient, right? Python has no "reify"
class FnHandler:
    implements(IHandler)

    def __init__(self, f):
        self.f = f

    def is_active(self):
        return True

    def commit(self):
        return self.f

# XXX
NONE = object()

class Process:
    def __init__(self, gen):
        self.gen = gen

    def _channel_responded(self, response):
        print response
        self.run(response)

    def run(self, response = NONE):
        if response is NONE:
            instruction = self.gen.next()
        else:
            instruction = self.gen.send(response)

        assert isinstance(instruction, Instruction)

        if instruction.op == "put":
            channel, value = instruction.data
            channel.put(value, FnHandler(self._channel_responded))
            return

        if instruction.op == "take":
            channel = instruction.data
            channel.take(FnHandler(self._channel_responded))


def put(channel, value):
    return Instruction("put", (channel, value))


def take(channel):
    return Instruction("take", channel)