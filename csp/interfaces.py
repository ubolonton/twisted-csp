from zope.interface import Interface

class IChannel(Interface):

    def take(self, handler):
        pass

    def put(self, value, handler):
        pass

    def close(self):
        pass


class IHandler(Interface):

    def is_active(self):
        pass

    def commit(self):
        pass


class IBuffer(Interface):

    def full(self):
        pass

    def remove(self):
        pass

    def add(self, item):
        pass
