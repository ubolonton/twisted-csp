from csp.impl import dispatch
from csp.impl.channels import ManyToManyChannel as Channel

# TODO: Check resolution
# TODO: Should be reactor-specific
# TODO: Some optimizations?

def timeout(seconds):
    channel = Channel()
    def done():
        channel.close()
    dispatch.queue_delay(done, seconds)
    return channel
