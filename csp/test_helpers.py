from twisted.internet import defer
import csp

def async(test_func):
    def asynced(self):
        d = defer.Deferred()
        ch = csp.spawn(test_func(self), chan=True)
        csp.take_then_callback(ch, d.callback)
        return d
    return asynced
