# http://talks.golang.org/2012/concurrency.slide#36
# Timeout for whole conversation using select

import csp

from .boring import boring

def main():
    c = boring("Joe")
    timeout = csp.timeout(5)
    while True:
        value, chan = yield csp.alts([c, timeout])
        if chan is c:
            print value
        else:
            print "You talk too much."
            yield csp.stop()
