# Quick and dirty convenient script to run the example
import sys
import os
from twisted.internet import reactor

def go(module):
    def start():
        print "Running", module
        print "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
        __import__(module)
    reactor.callWhenRunning(start)
    reactor.run()

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print "Module name required"
        exit(1)

    dirname = os.path.dirname(os.path.realpath(sys.argv[0]))
    path = os.path.join(dirname, "example")
    sys.path.insert(0, path)
    go(args[0])
    sys.path.pop(0)
