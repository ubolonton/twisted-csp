import csp

import sys

def main():
    chan = csp.Channel()
    chan.close()

    print (yield csp.take(chan))

    # This would blows up the stack if the implementation is in
    # correct (e.g. lack of dispatch.run in important places (see
    # Process._continue))
    limit = sys.getrecursionlimit()
    count = 0
    while True:
        count += 1
        yield csp.take(chan)
        if count > limit:
            print "Did not blow the stack"
            break
