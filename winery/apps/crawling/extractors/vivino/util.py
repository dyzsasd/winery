import hashlib


def href2id(href):
    addr = 'https://www.vivino.com' + href
    return url2id(addr)


def url2id(addr):
        return hashlib.md5(addr).hexdigest()
