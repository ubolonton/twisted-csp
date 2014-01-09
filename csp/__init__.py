from csp.process import Process, put, take, wait, alts

from csp.channels import ManyToManyChannel as Channel

def go(gen):
    process = Process(gen)
    process.run()
    return process
