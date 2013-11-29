import csp

from twisted.web.client import getPage


def request(url):
    return csp.channelify(getPage(url))


def main():
    def timeout_channel(seconds):
        c = csp.Channel()
        def _t():
            yield csp.wait(seconds)
            yield c.put(None)
        csp.go(_t())
        return c

    c = request("http://www.google.com/search?q=csp")
    t = timeout_channel(10)
    chan = yield csp.select(c, t)
    if chan is c:
        result, error = yield c.take()
        if error:
            print "Uhm, not good"
            print error
        else:
            print "Here"
            print result
    elif chan is t:
        print "Timeout"
