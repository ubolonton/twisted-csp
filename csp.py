from twisted.internet import reactor as global_reactor

import types

# TODO: Pull out the parts specific to twisted's event loop, add
# support for other event loops


# TODO: Instruction object
CHANNEL = "chan"
FUNCTION = "fn"
SPAWN = "spawn"
QUIT = "quit"
CALLBACKS = "callbacks"
WAIT = "wait"


# TODO: State object
CONTINUE = "continue"
SLEEP = "sleep"


class Channel:
    def __init__(self, size = None):
        # While +1?
        self.size = size + 1 if size else 1
        self.buffer = []
        # What is drain?
        self.drain = False

    def put(self, message):
        def do():
            if self.drain and len(self.buffer) == 0:
                self.drain = False
                return CONTINUE, None

            if len(self.buffer) < self.size:
                self.buffer.append(message)
                self.drain = (len(self.buffer) == self.size)
                if self.drain:
                    return SLEEP, None
                return CONTINUE, None

            return SLEEP, None
        return CHANNEL, do

    def take(self):
        def do():
            if len(self.buffer) == 0:
                return SLEEP, None
            return CONTINUE, self.buffer.pop()
        return CHANNEL, do


# FIX: This is so awkward
NONE = object()
class Process:
    def __init__(self, gen, reactor = global_reactor):
        self.reactor = reactor
        self.gen = gen
        self.subprocesses = []
        self._done = False
        self._next()

    def _next(self, message = NONE):
        try:
            if message is NONE:
                self.step = self.gen.next()
            else:
                self.step = self.gen.send(message)
        except StopIteration:
            self._stop()

    def _stop(self):
        if not self._done:
            # TODO: Do we really want this? How about detaching
            # subprocesses? Maybe this could be configurable
            for process in self.subprocesses:
                process._stop()
            self._done = True
            print self, "stopped"

    # FIX: This looks inefficient
    def _spin(self):
        self.reactor.callLater(0, self.run)

    def run(self):
        if self._done:
            return

        # TODO: Some better name, not "do"
        type, do = self.step

        if type == CHANNEL:
            state, message = do()
            assert state in (CONTINUE, SLEEP)
            if state == CONTINUE:
                self._next(message)
            self._spin()
            return

        if type == WAIT:
            seconds = do
            def wake_up():
                self._next()
                self._spin()
            self.reactor.callLater(seconds, wake_up)
            return

        # NOTE: Unused
        if type == CALLBACKS:
            def callback(message):
                self._next(message)
                self._spin()
            def errback(failure):
                # What if we don't unwrap?
                exception = failure.value
                self.step = self.gen.throw(exception)
                self._spin()
            do(callback, errback)
            return

        if type == SPAWN:
            self._next()
            self.subprocesses.append(do)
            self._spin()
            return

        if type == QUIT:
            self._stop()
            # TODO: Why spinning once more after stopping?
            self._spin()


def spawn(f, args, kwargs, reactor = global_reactor):
    gen = f(*args, **kwargs)
    process = Process(gen, reactor)
    process.run()
    return SPAWN, process


def process(reactor_or_f = global_reactor):
    """
    # Normal usage
    @process
    def foo():
        yield csp.wait(0.5)
        print (yield chan.take())

    # When twisted supports non-global reactor
    @process(custom_reactor)
    def foo():
        yield csp.wait(0.5)
        print (yield chan.take())
    """
    if isinstance(reactor_or_f, types.FunctionType):
        f = reactor_or_f
        def wrapped(*args, **kwargs):
            return spawn(f, args, kwargs, global_reactor)
        return wrapped
    else:
        reactor = reactor_or_f
        def decorator(f):
            def wrapped(*args, **kwargs):
                return spawn(f, args, kwargs, reactor)
            return wrapped
        return decorator


# TODO: Support something like Clojure core.async's alts!
def select(*channels):
    def do():
        # TODO: This is prioritizing channel that is listed first. Is
        # that desirable? No. Randomize an order first then check!
        for channel in channels:
            if len(channel.buffer) > 0:
                return CONTINUE, channel
        return SLEEP, None
    return CHANNEL, do


def wait(seconds):
    return WAIT, seconds


# TODO
def wrap(fn):
    def wrapped(*args, **kwargs):
        def do(callback):
            fn(callback, *args, **kwargs)
        return FUNCTION, do
    return wrapped


# TODO
def chanify(fn):
    def f(channel, *args, **kwargs):
        def ff(error, message):
            def gen():
                yield channel.put(message)
            spawn(gen)
        fn(channel, *args, **kwargs)
    return f


def quit():
    return QUIT, None
