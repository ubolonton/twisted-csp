# http://talks.golang.org/2012/concurrency.slide#25
# Generator: function that returns a channel

import csp
import random


def boring(message):
    channel = csp.Channel()
    def _do():
        i = 0
        while True:
            yield channel.put("%s %d" % (message, i))
            yield csp.wait(random.random())
            i += 1
    csp.go(_do())
    return channel


def main():
    b = boring("boring!")
    for i in range(5):
        print "You say: \"%s\"" % (yield b.take())
    print "You are boring; I'm leaving."