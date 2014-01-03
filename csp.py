import types
import Queue

from time import time

from twisted.internet import reactor as global_reactor
from twisted.internet.defer import Deferred, DeferredList


# TODO: Pull out the parts specific to twisted's event loop, add
# support for other event loops

# TODO: Maybe limit the number of processes/channels?

# TODO: Different buffer strategies like Clojure's core.async
# (dropping, sliding)

# TODO: Error mechanism? Convert errback back into exception? Throwing
# exception into the generator?


# TODO: Instruction object
SPAWN = "spawn"
QUIT = "quit"
CALLBACKS = "callbacks"
WAIT = "wait"
INFO = "info"

TAKE = "take"
PUT = "put"
TAKE_READY = "take_ready"
PUT_READY = "put_ready"
SELECT = "select"


# TODO: State object
CONTINUE = "continue"
SLEEP = "sleep"


# TODO: Add "close" functionality
class Channel:
    # TODO: How about unbounded channel?
    def __init__(self, size = 0):
        """Returns a new channel backed by a buffer of the specified size. If
        size is 0, putting/taking are synchronized.
        """
        if size > 0:
            self.buffer = Queue.Queue(size)
        else:
            self.buffer = None

        # TODO: Consider using deque to help with implementing
        # "select" (popping all the available queues, then "unpop" all
        # but one of them).

        # XXX: These queues have to be unlimited to accommodate all
        # pending readers/writers. Is there another lighter way?
        self.readers = Queue.Queue()
        self.writers = Queue.Queue()

        self.maybe_readers = set()
        self.maybe_writers = set()

    def put(self, message):
        return PUT, (self, message)

    def take(self):
        return TAKE, self

    def can_put(self):
        if not self.readers.empty():
            return True
        elif self.buffer and not self.buffer.full():
            return True
        else:
            return False

    def can_take(self):
        if not self.writers.empty():
            return True
        elif self.buffer and not self.buffer.empty():
            return True
        else:
            return False

    # TODO: Most of this logic should probably be handled by the
    # process, especially to implement "select"
    def flush(self):
        # print self, "flush"
        # FIX: This is a race condition if multiple threads are used.
        # Some sort of synchronization is needed (isn't the whole
        # thing supposed to be single-threaded though?)

        if self.buffer is None:
            while not (self.writers.empty() or self.readers.empty()):
                writer, value = self.writers.get()
                reader = self.readers.get()
                writer.callback(None)
                reader.callback(value)
        else:
            while True:
                if not (self.buffer.empty() or self.readers.empty()):
                    value = self.buffer.get()
                    reader = self.readers.get()
                    reader.callback(value)
                    continue
                if not (self.writers.empty() or self.buffer.full()):
                    writer, value = self.writers.get()
                    self.buffer.put(value)
                    writer.callback(None)
                    continue
                break

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
        # print self, "next", message
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

    def _spin(self):
        self.reactor.callLater(0, self.run)

    def _got_message(self, message):
        print self, "got", message
        self._next(message)
        self._spin()

    def run(self):
        if self._done:
            return

        # TODO: Some better name, not "do"
        type, do = self.step
        print self, self.step

        if type == PUT:
            channel, message = do
            writer = Deferred()
            writer.addCallback(self._got_message)
            channel.writers.put((writer, message))
            self.reactor.callLater(0, channel.flush)
            return

        if type == TAKE:
            channel = do
            reader = Deferred()
            reader.addCallback(self._got_message)
            channel.readers.put(reader)
            self.reactor.callLater(0, channel.flush)
            return

        # So one of the operations we were SELECTing on is ready,
        # cancel stop looking
        def _cancel_alls(_, deferreds):
            for v, channel, d in deferreds:
                assert v in ("writer", "reader")
                if v == "writer":
                    channel.maybe_writers.remove(d)
                elif v == "reader":
                    channel.maybe_readers.remove(d)

        def _ready_write(channel, operations, maybe_writer, message):
            # channel.maybe_writers.remove(maybe_writer)

            # XXX: Yup, race conditions are everywhere. Anyway, we
            # need to check again because some other process waiting
            # to write on the channel may have proceeded already.
            if channel.can_put():
                writer = Deferred()
                writer.addCallback(self._got_message)
                channel.writers.put((writer, message))
                self.reactor.callLater(0, channel.flush)
            else:
                # maybe_writer = Deferred()
                # maybe_writer.addCallback(_ready_write, maybe_writer, message)
                # channel.maybe_writers.add(maybe_writer)

                # Another process got their first, start SELECTing all
                # over again :(
                # FIX: This is simple but inefficient. It's better to
                # stop looking at other operations only if this one
                # can actually go forward
                _do_select(operations)

            # Similar to _ready_write
        def _ready_read(channel, operations, maybe_reader):
            if channel.can_take():
                reader = Deferred()
                reader.addCallback(self._got_message)
                channel.readers.put(reader)
                self.reactor.callLater(0, channel.flush)
            else:
                _do_select(operations)

        def _do_select(operations):
            deferreds = []
            # Tell the channels we "may be" interested in these
            # operations
            for op, data in operations:
                assert op in (PUT, TAKE)
                if op == PUT:
                    channel, message = data
                    # TODO
                    maybe_writer = Deferred()
                    maybe_writer.addCallback(_ready_write, operations, maybe_writer, message)
                    channel.maybe_writers.add(maybe_writer)
                    deferreds.append(("writer", channel, maybe_writer))
                elif op == TAKE:
                    channel =  data
                    # TODO
                    maybe_reader = Deferred()
                    maybe_reader.addCallback(_ready_write, operations, maybe_reader)
                    channel.maybe_readers.add(maybe_reader)
                    deferreds.append(("reader", channel, maybe_reader))

            # TODO: Indeterminism, if needed, should be specified here
            # (e.g. shuffle the deferred list), right?

            # Go ahead with the first one that responds
            ds = DeferredList([d for _, _, d in deferreds], fireOnOneCallback = True)
            ds.addCallback(_cancel_alls)

        if type == SELECT:
            operations = do
            _do_select(operations)
            return

        if type == WAIT:
            # print self, "wait"
            seconds = do
            def wake_up(start):
                end = time()
                message = start, end
                self._next(message)
                self._spin()
            self.reactor.callLater(seconds, wake_up, time())
            return

        if type == INFO:
            message = do(self)
            self._next(message)
            self._spin()
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

        # TODO: Shouldn't client code decide how to wire processes?
        if type == SPAWN:
            self._next()
            self.subprocesses.append(do)
            self._spin()
            return

        if type == QUIT:
            self._stop()
            # TODO: Why spinning once more after stopping?
            self._spin()


def go(gen, reactor = global_reactor):
    """Takes a generator that generates instructions, run the
    associated code in a pseudo-thread (lightweight process).
    Returns a SPAWN instruction.
    """
    process = Process(gen, reactor)
    process.run()
    return SPAWN, process


def spawn(f, args, kwargs, reactor = global_reactor):
    gen = f(*args, **kwargs)
    return go(gen, reactor)


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


def take(channel):
    return TAKE, channel


def put(channel, message):
    return PUT, (channel, message)


def select(*operations):
    # raise Exception("Not implemented yet")
    return SELECT, operations


def wait(seconds):
    """Usage:
    yield wait(2)

    "Returns" a tuple of start time and end time of the wait.
    """
    return WAIT, seconds


def channelify(d):
    """Takes a Twisted deferred, returns a channel that can be taken from.
    """
    channel = Channel()
    # TODO: Maybe better error handling?
    @process
    def ok(value):
        yield channel.put((value, None))
    @process
    def error(failure):
        yield channel.put((None, failure))
    # TODO: Add a control to be able to cancel the deferred (by
    # closing maybe?)
    d.addCallback(ok)
    d.addErrback(error)
    return channel


def multi_channelify(d):
    """Takes a Twisted deferred, returns 2 channels that can be taken from:
    a value channel and an error channel.
    """
    v_channel = Channel()
    e_channel = Channel()
    # TODO: Maybe better error handling?
    @process
    def ok(value):
        yield v_channel.put(value)
    @process
    def error(failure):
        yield e_channel.put(failure)
    d.addCallback(ok)
    d.addErrback(error)
    return v_channel, e_channel


def quit():
    return QUIT, None


# TODO: Are these useful at all?

def get_current_process():
    return INFO, lambda self: self


def get_current_reactor():
    return INFO, lambda self: self.reactor


def get_subprocesses():
    return INFO, lambda self: tuple(self.subprocesses)


def stop():
    return INFO, lambda self: self._stop()


# This may work, but it's kind of bizarre (and hard to debug).
# Actually it would not work, because of the extra "next" call
def wait1(seconds):
    from time import time
    def do_wait(self):
        def wake_up(start):
            end = time()
            message = end - start
            self._next(message)
            self._spin()
        start = time()
        self.reactor.callLater(seconds, wake_up, start)
    return INFO, do_wait
