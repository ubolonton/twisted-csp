#!/usr/bin/env python
# Quick and dirty convenient script to run the example
import sys
from twisted.internet import reactor

example = "example"

def run_twisted_then_load(module):
    def start():
        print "Running", "/".join([example, module])
        print
        __import__(example, fromlist=[module])
    reactor.callWhenRunning(start)
    reactor.run()

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print "Module name required"
        exit(1)

    run_twisted_then_load(args[0])
