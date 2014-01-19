# http://talks.golang.org/2012/concurrency.slide#35
# Timeout using select

import csp

from .boring import boring

def main():
    c = boring("Joe")
    while True:
        value, chan = yield csp.alts([c, csp.timeout(0.8)])
        if chan is c:
            print value
        else:
            print "You're too slow."
            yield csp.stop()
