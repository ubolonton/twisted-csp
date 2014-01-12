import csp

from twisted.web.client import getPage


def request(url):
    channel = csp.Channel(1)
    def ok(value):
        csp.put_then_callback(channel, (value, None), csp.no_op)
    def error(failure):
        csp.put_then_callback(channel, (None, failure), csp.no_op)
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
        t = csp.timeout(dt)
        value, chan = yield csp.alts([c, t])
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
