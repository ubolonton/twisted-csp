Communicating sequential processes for Twisted. Channels like Go, or Clojure `core.async`.

**WARNING: This is currently a toy.**

# Requirements
Twisted

# Examples
Function returning channel (http://talks.golang.org/2012/concurrency.slide#25).
```python
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
```

Pingpong (http://talks.golang.org/2013/advconc.slide#6).
```python
class Ball:
    hits = 0

def player(name, table):
    while True:
        ball = yield table.take()
        ball.hits += 1
        print name, ball.hits
        yield csp.wait(0.1)
        yield table.put(ball)

def main():
    table = csp.Channel()

    yield csp.go(player("ping", table))
    yield csp.go(player("pong", table))

    yield table.put(Ball())
    yield csp.wait(1)
```
# Running the examples
Use the `run` script, like
```bash
./run example.go.pingpong
```

# Playing around in a REPL
```python
Python 2.7.5+ (default, Sep 19 2013, 13:48:49)
[GCC 4.8.1] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import thread
>>> from twisted.internet import reactor
>>> thread.start_new_thread(reactor.run, (), {"installSignalHandlers": False})
139751934256896
>>> from csp import *
>>> class Ball:
...     hits = 0
...
>>> def player(name, table):
...     while True:
...         ball = yield table.take()
...         ball.hits += 1
...         print name, ball.hits
...         yield wait(0.1)
...         yield table.put(ball)
...
>>> @process
... def main():
...     table = Channel()
...     yield go(player("ping", table))
...     yield go(player("pong", table))
...     yield table.put(Ball())
...     yield wait(1)
...
>>> reactor.callFromThread(main)
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
<csp.Process instance at 0x1274e18> stopped
<csp.Process instance at 0x1274ef0> stopped
<csp.Process instance at 0x1274c68> stopped

>>>
```

Examples under `example/go` are ported from Go examples:
- http://talks.golang.org/2012/concurrency.slide
- http://talks.golang.org/2013/advconc.slide.

# Documentation

## Channels
Unbuffered: puts and takes are synchronized. A reader waits until a writer arrives, and vice-versa.
```python
csp.Channel()
```
Buffered: puts and takes can be asynchronous. A reader proceeds if the queue is not empty, a writer proceeds if the queue is not full.
```python
csp.Channel(size = 2)
```

Channel operations must happen inside "light-weight processes", which are simulation of execution threads, using generators following certain conventions.

## yield channel.put(object)
Put an object on the channel. If the channel is full, or unbuffered, wait until an object is taken off the channel, or when another process tries to take from the channel.

## yield channel.take()
Take an object off the channel. If the channel is empty, or unbuffered, wait until something is put on the channel.

## yield csp.wait(seconds)
Suspend the current process without blocking the real thread.
```python
def slow_pipe(in, out):
    v = yield in.take()
    yield csp.wait(0.5)
    yield out.put(v)
```

## yield csp.select(*channels)
Choose the first channel that is ready to be taken from, waiting until at least one is ready.
```python
def test(url):
    def timeout_channel(seconds):
        c = csp.Channel()
        def _t():
            yield csp.wait(seconds)
            yield c.put(None)
        csp.go(_t())
        return c

    g = google_channel(url)
    d = duckduckgo_channel(url)
    t = timeout_channel(5)
    chan = yield csp.select(g, d, t)
    if chan is g:
        print "Google is fast"
        print yield chan.take()
    elif chan is d:
        print "Duckduckgo is fast"
        print yield chan.take()
    else:
        print "Search engines are slow"
```

## csp.go(gen)
Spawn a lightweight process given a generator.
```python
def pipe(in, out):
    v = yield in.take()
    yield out.put(v)

go(pipe(search, log))
```

## csp.process(f)
Decorate a generator function so that calling it spawns a process.
```python
@process
def pipe(in, out):
    v = yield in.take()
    yield out.put(v)

pipe(search, log)
```

## csp.channelify(deferred)
Convert a Twisted deferred into a channel. A tuple of `(value, failure)` will be put on the channel once the deferred finishes.
```python
from twisted.web.client import getPage
def google(term):
    c = csp.channelify(getPage("http://www.google.com/search?q=%s" % term))
    result, error = yield c.take()
    if error:
        print "Uhm, not good:"
        print error
    else:
        print "Google search results:"
        print result
```

# TODO
- Proper implementation of channel operations (each channel needs to keep track of pending readers/writers). The current implementation simply polls repeatedly. While it may appear to work, it is (at least) not efficient.
- Closeable channels.
- Support for selecting over all channel operations, instead of just taking.
- More fine-grained control of processes.
- More examples.

# Limitations
- No "deep" yield. Therefore it is impossible to extract pieces of
  logic that does channel communication without spawning a new process
  (maybe python 3 ("yield from") will help?). This can reduce composability.
- There must be running event loop.
- Channel's normal API cannot be used outside of a process (more
  precisely outside of the generator function of a process). Another
  set of API would be needed for that.
- Cooperative scheduling (usually this is not a big problem).
- Forgetting to yield causes bug (value not being put on channel,
  infinite loop blocking thread (Go/Clojure do not have this problem
  because single syntactic units are used there, as opposed to "yield"
  plus something)).
- Select API is clunky without first-class language support (built-in like Go, or through macro in Clojure).

# Inspiration
- http://swannodette.github.io/2013/08/24/es6-generators-and-csp
- https://github.com/clojure/core.async
- https://github.com/olahol/node-csp

Other Python CSP libraries:
- http://code.google.com/p/pycsp/
- https://github.com/python-concurrency/python-csp
- https://github.com/stuglaser/pychan

These libraries use threads/processes (except for pycsp, which has support for greenlets (which is not portable)). This makes implementation simpler (in principle), sacrificing efficiency (but managing threads/processes can be a chore). On the other hand they are much more generic, and support networked channels (that is not necessarily a good thing though).
TODO: More elaborate comparison.
