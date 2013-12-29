import csp

class Ball:
    hits = 0


def player(delay, table):
    hits = 0
    while True:
        trainer = yield table.take()
        hits += 1
        print trainer, " => ", "player"
        yield csp.wait(delay)


def trainer(name, delay, table):
    while True:
        # print name, " => "
        yield table.put(name)
        yield csp.wait(delay)


def main():
    # Size of buffer: the 2 guns ensure no more than X balls are
    # flying at the same time (so as not to overwhelm the player :D)
    table = csp.Channel(1)

    yield csp.go(player(0.1, table))
    yield csp.go(trainer("quick gun", 0.01, table))
    yield csp.go(trainer("slow gun", 0.2, table))

    yield csp.wait(2)
