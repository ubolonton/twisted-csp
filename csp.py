from twisted.internet import reactor

# TODO: Instruction object
CHANNEL = "chan"
FUNCTION = "fn"
SPAWN = "spawn"
QUIT = "quit"
CALLBACKS = "callbacks"


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

    # def ready(self):
    #     return len(self.buffer) > 0

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
    def __init__(self, gen):
        self.gen = gen
        self._done = False
        self.subprocesses = []
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
        reactor.callLater(0, self.run)

    def run(self):
        if self._done:
            return

        # value = self.step
        # print "value:", value
        # type, do = self.value
        type, do = self.step

        if type == CHANNEL:
            state, message = do()
            assert state in (CONTINUE, SLEEP)
            if state == CONTINUE:
                self._next(message)
            self._spin()
            return

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

        if type == FUNCTION:
            # TODO: Change into callback/errback
            def f(error, message):
                if error:
                    self.step = self.gen.throw(error)
                else:
                    self._next(message)
                self._spin()
            do(f)
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


def spawn(f, *args, **kwargs):
    gen = f(*args, **kwargs)
    process = Process(gen)
    process.run()
    return SPAWN, process


def process(f):
    def wrapped(*args, **kwargs):
        return spawn(f, *args, **kwargs)
    return wrapped


def select(*channels):
    def do():
        # TODO: This is prioritizing channel that is listed first. Is
        # that desirable?
        for channel in channels:
            if len(channel.buffer) > 0:
                return CONTINUE, channel
        return SLEEP, None
    return CHANNEL, do


def wait(seconds):
    def do(callback, _):
        reactor.callLater(seconds, callback, None)
    return CALLBACKS, do


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


def test(f, *args, **kwargs):
    reactor.callWhenRunning(f, *args, **kwargs)
    reactor.run()
