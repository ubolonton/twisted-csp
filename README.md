Communicating sequential processes for Twisted. Channels like Go, or Clojure `core.async`.

**WARNING: This is currently a toy.**

# Requirements
Twisted

# Running the examples
Use the `run` script, like
```bash
./run example.go.pingpong
```

Examples under `example/go` are ported from Go examples:
- http://talks.golang.org/2012/concurrency.slide
- http://talks.golang.org/2013/advconc.slide.

# Documentation

Channel operations must happen inside "light-weight processes", which are simulation of execution threads, using generators following certain conventions.

## Create a channel
Unbuffered: puts and takes are synchronized. A reader waits until a writer arrives, and vice-versa.
```python
csp.Channel()
```
Buffered: puts and takes can be asynchronous. A reader proceeds if the queue is not empty, a writer proceeds if the queue is not full.
```python
csp.Channel(size = 2)
```

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

## csp.channelify(deferred)
Convert a Twisted deferred into a channel. A tuple of `(value, failure)` will be put on the channel once the deferred finishes.
```python
from twisted.web.client import getPage
def google(url):
    c = csp.channelify(getPage(url))
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
