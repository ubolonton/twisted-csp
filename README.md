# Twisted CSP
Communicating sequential processes for Twisted. Channels like Go, or Clojurescript's `core.async`.

**WARNING: This is currently alpha  software.**

This is a very close port of Clojurescript's `core.async`. The significant difference is that light-weight processes are implemented using generators (`yield`) instead of macros.

- Channel operations must happen inside "light-weight processes" (code flows, not actual threads).
- Light-weight processes are spawn by calling `go`, `go_channel`, `go_deferred` or by using their decorator equivalents.
- Most channel operations must follow the form of `yield do_sth(...)`.

```python
def slow_pipe(input, output):
    while True:
        value = yield take(input)
        yield sleep(0.5)
        if value is None: # input closed
            close(output)
            yield stop()
        else:
            yield put(output, value)

go(slow_pipe, chan1, chan2))
```

## Examples ##

Function returning channel (http://talks.golang.org/2012/concurrency.slide#25).
```python
def boring(message):
    c = Channel()
    def counter():
        i = 0
        while True:
            yield put(c, "%s %d" % (message, i))
            yield sleep(random.random())
            i += 1
    go(counter)
    return c


def main():
    b = boring("boring!")
    for i in range(5):
        print "You say: \"%s\"" % (yield take(b))
    print "You are boring; I'm leaving."
```

Pingpong (http://talks.golang.org/2013/advconc.slide#6).
```python
class Ball:
    hits = 0


@process
def player(name, table):
    while True:
        ball = yield take(table)
        ball.hits += 1
        print name, ball.hits
        yield sleep(0.1)
        yield put(table, ball)


def main():
    table = Channel()

    player("ping", table)
    player("pong", table)

    yield put(table, Ball())
    yield sleep(1)
```

Timeout using `alts` (`select` in Go) (http://talks.golang.org/2012/concurrency.slide#35).
```python
c = boring("Joe")
while True:
    value, chan = yield alts([c, timeout(0.8)])
    if chan is c:
        print value
    else:
        print "You're too slow."
        yield stop()
```

## Running the examples ##

Use the `run` script, like
```bash
./run example.go.timeout_for_whole_conversation_using_select
```

Examples under `example/go` are ports of Go examples from:
- http://talks.golang.org/2012/concurrency.slide
- http://talks.golang.org/2013/advconc.slide.


## Playing around in a REPL ##

```python
Python 2.7.5+ (default, Sep 19 2013, 13:48:49)
[GCC 4.8.1] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import thread
>>> from csp import *
>>> from twisted.internet import reactor
>>> thread.start_new_thread(reactor.run, (), {"installSignalHandlers": False})
140038185355008
>>> class Ball:
...     hits = 0
...
>>> def player(name, table):
...     while True:
...         ball = yield take(table)
...         if ball is None: # channel's closed
...             print name, "Ball's gone"
...             break
...         ball.hits += 1
...         print name, ball.hits
...         yield sleep(0.1)
...         yield put(table, ball)
...
>>> def main():
...     table = Channel()
...     go(player, "ping", table)
...     go(player, "pong", table)
...     yield put(table, Ball())
...     yield sleep(1)
...     close(table)
...
>>> reactor.callFromThread(lambda: go(main))
>>> ping 1
pong 2
ping 3
pong 4
ping 5
pong 6
ping 7
pong 8
ping 9
pong 10
ping Ball's gone
pong Ball's gone

>>>
```

## Limitations ##

- Does not work in a multi-threaded environment, at all (this is fixable though).
- Channel's normal API cannot be used outside of a process (more precisely outside of the generator function of a process).
- Generator functions must be used to spawn processes. This makes it less composable than in Go (where the constructs are built-in), or Clojurescript (where macros rule).
- Forgetting to `yield` can cause subtle bugs.
- Cooperative multi-processing (not sure if this is a big problem though).

## TODO ##

- Multiplexing, mixing, publishing/subscribing.
- Channel operations (map, filter, reduce...).
- Support multi-threaded environment (porting Clojure's `core.async` not Clojurescript's).
- Write **tests**.
- Think of a sensible error handling strategy (I think this should be decided by client code not library code though).
  + Should there be a separate error channel?
  + Should channels deliver `(result, error)` tuples?
  + Should errors be treated as special values (caught exceptions [re-thrown when taken](http://swannodette.github.io/2013/08/31/asynchronous-error-handling/))?
- Support other reactors, e.g. [Tornado](http://www.tornadoweb.org/en/stable/) (should be easy, as the dispatcher is the only thing that depends on twisted).
- More documentation.
- More examples (focusing on leveraging Twisted's rich network capabilities).
- `put_then_callback`, `take_then_callback` execute the supplied callback in the same tick if result is immediately available. This can cause problems (especially if they are public API).

## Inspiration ##

- http://swannodette.github.io/2013/08/24/es6-generators-and-csp
- https://github.com/clojure/core.async
- https://github.com/olahol/node-csp

Other Python CSP libraries:
- http://code.google.com/p/pycsp/
- https://github.com/python-concurrency/python-csp
- https://github.com/stuglaser/pychan

These libraries use threads/processes (except for pycsp, which has support for greenlets (which is not portable)). This makes implementation simpler (in principle), sacrificing efficiency (but managing threads/processes can be a chore). On the other hand they are much more generic, and support networked channels (that is not necessarily a good thing though).
TODO: More elaborate comparison.
