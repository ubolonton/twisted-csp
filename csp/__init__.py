from csp.process import Process, put, take, wait, alts

from csp.channels import ManyToManyChannel as Channel

def go(gen):
    process = Process(gen)
    process.run()
    return process


# For API consistency (sort of)
def close(channel):
    return channel.close()
