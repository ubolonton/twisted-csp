from zope.interface import Interface

# TODO: These interfaces are nowhere nearly as powerful as Clojure's
# protocols (e.g. no reify). I'm not sure they are even worth it
# except for maybe documentation.

class IChannel(Interface):

    def take(self, handler):
        pass

    def put(self, value, handler):
        pass

    def close(self):
        pass

    def is_closed(self):
        pass


class IHandler(Interface):

    def is_active(self):
        pass

    def commit(self):
        pass


class IBuffer(Interface):

    def is_full(self):
        pass

    def remove(self):
        pass

    def add(self, item):
        pass
