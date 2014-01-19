# http://talks.golang.org/2012/concurrency.slide#26
# Channels as a handle on a service

import csp

from .boring import boring


def main():
    joe = boring("Joe")
    ann = boring("Ann")
    for i in range(5):
        print "\"%s\"" % (yield csp.take(joe))
        print "\"%s\"" % (yield csp.take(ann))
    print "You are boring; I'm leaving."
