# http://talks.golang.org/2012/concurrency.slide#36
# Timeout for whole conversation using select

from csp import timeout, stop, alts

from .boring import boring

def main():
    c = boring("Joe")
    t = timeout(5)
    while True:
        value, chan = yield alts([c, t])
        if chan is c:
            print value
        else:
            print "You talk too much."
            yield stop()
