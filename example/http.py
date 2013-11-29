import csp

from twisted.web.client import getPage


def excerpt(text, cutoff=100):
    l = len(text)
    if l > cutoff:
        return text[0:cutoff] + "..."
    else:
        return text


def request(url):
    return csp.tagged_channelify(getPage(url))


def main():
    c = request("http://google.com")
    result, error = yield c.take()
    if error:
        print "Uhm, not good"
        print error
    else:
        print "Here"
        print excerpt(result)
