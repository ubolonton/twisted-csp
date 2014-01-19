from twisted.internet import reactor

from csp.impl.buffers import RingBuffer

class TwistedDispatcher:

    TASK_BATCH_SIZE = 1024

    def __init__(self):
        self.tasks = RingBuffer(32)
        self.running = False
        self.queued = False

    def run(self, f):
        # TODO: Should there be some sort of limit?
        self.tasks.unbounded_unshift(f)
        self.queue()

    def queue_delay(self, f, seconds):
        reactor.callLater(seconds, f)

    def process_messages(self):
        self.running = True
        self.queued = False
        count = 0
        while True:
            try:
                task = self.tasks.pop()
            except IndexError:
                break

            task()

            # TODO: Maybe stop after a max amount of time rather than
            # a max number of tasks.
            count += 1
            if count >= self.TASK_BATCH_SIZE:
                break

        self.running = False
        if len(self.tasks) > 0:
            self.queue()

    def queue(self):
        if self.queued and self.running:
            return

        self.queued = True
        reactor.callLater(0, self.process_messages)

# TODO: Support other dispatchers (e.g. tornado or other reactors)
dispatcher = TwistedDispatcher()

run = dispatcher.run

queue_delay = dispatcher.queue_delay
