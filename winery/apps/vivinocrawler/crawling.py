import gzip
import hashlib
import urllib2
from StringIO import StringIO

from lxml import etree
import lxml.html as lh

from winery.apps.vivinocrawler.models import Win

SITE_MAP_ADDR = 'https://www.vivino.com/sitemap.xml'

HASHER = hashlib.md5()


class FetchTask(object):
    content = None
    status = None 

    def __init__(self, url):
        self.url = url

    def fetch(self):
        try:
            handle = urllib2.urlopen(self.url)
        except urllib2.HTTPError:
            self.content = 404
        self.status = handle.code
        self.content = handle.read()
        self.tree = lh.fromstring(self.content)

    def parse(self):
        pass


class WineryTask(FetchTask):
    def parse(self):
        name = ''.join(self.tree.xpath('//h1[@itemprop="name"]/text()'))
        contry = ''.join(
            self.tree.xpath(
                '//span[@class="country semi"]'
                '/meta[@itemprop="addressCountry"]/@content'
            )
        )
        country_href = ''.join(
            self.tree.xpath(
                '//span[@class="country semi"]/a/@href'
            )
        )
        country_id = _compose_parse(addr, country_href)
        region = ''.join(
            self.tree.xpath(
                '//span[@itemprop="addressRegion"]/a/text()'
            )
        )
        region_href = ''.join(
            self.tree.xpath(
                '//span[@itemprop="addressRegion"]/a/@href'
            )
        )
        region_id = _compose_parse(addr, region_href)
        win_count = ''.join(self.tree.xpath(
            'div[@class="average-price"]/h2/text()'))
        rating = ''.join(self.tree.xpath(
            'h2[@itemprop="ratingValue"]/text()'))
        description = ""


class WinTask(FetchTask):
    pass


class RegionTask(FetchTask):
    pass


class CountryTask(FetchTask):
    pass


class GrapTask(FetchTask):
    pass


def _compose_parse(addr, href):
    comps = addr.split('/')
    new_addr = '/'.join(comps[:3]) + href
    HASHER.update(new_addr)
    return HASHER.hexdigest()


rubs = {}


def main():
    nsp = {'sitemap':'http://www.sitemaps.org/schemas/sitemap/0.9'}
    top_map = urllib2.urlopen(SITE_MAP_ADDR).read()
    tree = etree.fromstring(top_map)
    locs = tree.xpath('//sitemap:loc', namespaces=nsp)
    print 'Get %d sitmaps' % len(locs)
    count = 0
    for loc in locs:
        print 'crawling sitmap %d with %s' % (count, loc.text)
        request = urllib2.Request(loc.text)
        request.add_header('Accept-encoding', 'gzip')
        try:
            response = urllib2.urlopen(request)
        except Exception as e:
            print e
            continue
        if 'gzip' in response.info().get('Content-Type'):
            try:
                buf = StringIO(response.read())
                f = gzip.GzipFile(fileobj=buf)
                data = f.read()
            except Exception as e:
                print e
                continue
            url_tree = etree.fromstring(data)
            print 'get %d page urls' % len(url_tree.getchildren())
            for url in url_tree.getchildren():
                for url_loc in url.xpath('sitemap:loc', namespaces=nsp):
                    addr = url_loc.text
                    _crawl(addr)
        count += 1
        print rubs
    print rubs


def _crawl(addr):
    components = addr.split('/')
    if len(components) > 3:
        rub = components[3]
        if rub not in rubs:
            rubs[rub] = 0
        rubs[rub] += 1
        task = None
#        if rub == 'wineries':
#            task = WineryTask(addr)
#        if task:
#            task.get()



if __name__ == '__main__':
    main()
