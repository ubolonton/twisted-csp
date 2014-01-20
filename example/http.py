from csp import Channel, alts, timeout, put_then_callback, no_op

from twisted.web.client import getPage


def request(url):
    channel = Channel(1)
    def ok(value):
        put_then_callback(channel, (value, None), no_op)
    def error(failure):
        put_then_callback(channel, (None, failure), no_op)
    getPage(url).addCallback(ok).addErrback(error)
    return channel


def main():
    for url, dt in (
        ("http://www.google.com/search?q=csp", 0.01), # too little time
        ("http://www.google.come/search?q=csp", 10),  # wrong domain name
        ("http://www.google.com/search?q=csp", 10),
    ):
        print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
        print url, dt, "seconds"
        c = request(url)
        t = timeout(dt)
        value, chan = yield alts([c, t])
        if chan is c:
            result, error = value
            if error:
                print "Uhm, not good"
                print error
            else:
                print "Here"
                print result[:500] + "..."
        elif chan is t:
            print "Timeout"
