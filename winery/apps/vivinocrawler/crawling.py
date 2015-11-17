import gzip
import time
import urllib2
from StringIO import StringIO
import re

from lxml import etree
import lxml.html as lh

from winery.apps.vivinocrawler.models import *
from winery.apps.vivinocrawler.util import href2id

SITE_MAP_ADDR = 'https://www.vivino.com/sitemap.xml'

rubs = {}

chiffre_regex = re.compile(r'[\d,]+')


def main():
    nsp = {'sitemap':'http://www.sitemaps.org/schemas/sitemap/0.9'}
    top_map = urllib2.urlopen(SITE_MAP_ADDR).read()
    tree = etree.fromstring(top_map)
    locs = tree.xpath('//sitemap:loc', namespaces=nsp)
    print 'Get %d sitemaps' % len(locs)
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
                    print 'process %s' % addr
                    _crawl(addr)
                    #time.sleep(3)
        count += 1
        print rubs
    print rubs


def _crawl(addr):
    components = addr.split('/')
    if len(components) > 3:
        rub = components[3]
        task = None
        if rub == 'wine-countries':
            task = CountryTask(addr)
        elif rub == 'wine-regions':
            task = RegionTask(addr)
        elif rub == 'wineries':
            if len(components) > 5 and components[5] == 'wines':
                task = WinTask(addr)
            else:
                task = WineryTask(addr)
        elif rub == 'grapes':
            task = GrapTask(addr)
    if task:
        document = task.parse()
        document.save()


if __name__ == '__main__':
    main()


class cached_property(object):
    def __init__(self, func):
        self.__doc__ = getattr(func, '__doc__')
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value


class FetchTask(object):
    def __init__(self, url):
        self.url = url

    def _fetch(self):
        content = ''
        try:
            content = urllib2.urlopen(self.url).read()
        except urllib2.HTTPError:
            content = 404
        return content

    @cached_property
    def tree(self):
        return lh.fromstring(self._fetch())

    def parse(self):
        pass


class CountryTask(FetchTask):
    def parse(self):
        url = self.url
        raw_name = [country.strip() for country
                    in self.tree.xpath('//h1/text()')]
        name = ''.join(raw_name)
        geo_query = ''.join(
            [query.strip() for query
             in self.tree.xpath('//*[@id="country-map"]/@data-query')])
        print name
        return Country(
            url = url,
            name = name,
            geo_query = geo_query
        )


class RegionTask(FetchTask):
    def parse(self):
        url = self.url
        raw_name = [country.strip() for country
                    in self.tree.xpath('//h1/text()')]
        name = ''.join(raw_name)
        geo_query = ''.join(
            [query.strip() for query
             in self.tree.xpath('//*[@id="region-map"]/@data-query')])

        name_list = self.tree.xpath(
            '//div[@class="location"]//li//h3/a/text()')

        id_list = [href2id(href) for href in
            self.tree.xpath('//div[@class="location"]//li//h3/a/@href')]

        country_name = (name_list and name_list[0]) or ''
        country_id = (id_list and id_list[0]) or ''

        parent_name = (name_list[1:] and name_list[-1]) or ''
        parent_id = (id_list[1:] and id_list[-1]) or ''

        ancestor_region_names = '-'.join(name_list)
        ancestor_region_ids = '-'.join(id_list)

        niveau = len(name_list) or -1

        return Region(
            url = url,
            name = name,
            geo_query = geo_query,
            country_name = country_name,
            country_id = country_id,
            parent_name = parent_name,
            parent_id = parent_id,
            ancestor_region_names = ancestor_region_names,
            ancestor_region_ids = ancestor_region_ids,
            niveau = niveau
        )


class WineryTask(FetchTask):
    def parse(self):
        url = self.url
        raw_name = [country.strip() for country
                    in self.tree.xpath('//h1/text()')]
        name = ''.join(raw_name)
        raw_country_name = self.tree.xpath(
            '//span[meta/@itemprop="addressCountry"]/a/text()'
        )
        country_name = (raw_country_name and raw_country_name[0]) or ''
        country_id = href2id(''.join(
            self.tree.xpath(
                '//span[meta/@itemprop="addressCountry"]/a/@href'
            )
        ))
        raw_region_name = self.tree.xpath(
            '//span[@itemprop="addressRegion"]/a/text()'
        )
        region_name = (raw_region_name and raw_region_name[0]) or ''
        region_id = href2id(''.join(
            self.tree.xpath(
                '//span[@itemprop="addressRegion"]/a/@href'
            )
        ))
        raw_rating = [
            chiffre for chiffre_text in
            self.tree.xpath('//*[@itemprop="ratingValue"]/text()')
            for chiffre in chiffre_regex.findall(chiffre_text)
        ]
        raw_count = [
            chiffre for chiffre_text in
            self.tree.xpath('//*[@itemprop="ratingCount"]/@content')
            for chiffre in chiffre_regex.findall(chiffre_text)
        ]

        rating = (raw_rating and float(raw_rating[0].replace(',', '.'))) or -1
        count = (raw_count and float(raw_count[0].replace(',', '.'))) or -1
        websites = self.tree.xpath(
            '/html/body/div[2]/section[1]/div'
            '/div[3]/div[1]/section[2]/div/div/a/@href')

        address = ''.join(self.tree.xpath(
            '//*[@itemprop="streetAddress" '
            'or @itemprop="postalCode" or '
            '@itemprop="addressLocality"]/text()'))

        description = ""

        return Winery(
            url = url,
            name = name,
            country_name = country_name,
            country_id = country_id,
            region_name = region_name,
            region_id = region_id,
            rating_value = rating,
            rating_count = count,
            address = address,
            websites = websites,
            description = description
        )


class WinTask(FetchTask):
    def parse(self):
        url = self.url
        name_list = self.tree.xpath('//h1[@itemprop="name"]/span/text()')
        name = ' '.join(name_list[:-1])
        year = name_list[-1]
        raw_country_name = self.tree.xpath(
            '//a[@data-item-type="Country"]/text()'
        )
        country_name = (raw_country_name and raw_country_name[0]) or ''
        country_id = href2id(''.join(
            self.tree.xpath(
                '//a[@data-item-type="Country"]/@href'
            )
        ))
        raw_region_name = self.tree.xpath(
            '//a[@data-item-type="wine-region"]/text()'
        )
        region_name = (raw_region_name and raw_region_name[0]) or ''
        region_id = href2id(''.join(
            self.tree.xpath(
                '//a[@data-item-type="wine-region"]/@href'
            )
        ))
        raw_rating = [
            chiffre for chiffre_text in
            self.tree.xpath(
                '//*[@data-track-type="wi"]'
                '//*[@itemprop="aggregateRating"]'
                '//*[@itemprop="ratingValue"]/text()')
            for chiffre in chiffre_regex.findall(chiffre_text)
        ]
        raw_count = [
            chiffre for chiffre_text in
            self.tree.xpath(
                '//*[@data-track-type="wi"]'
                '//*[@itemprop="price"]'
                '//*[@itemprop="ratingCount"]/text()')
            for chiffre in chiffre_regex.findall(chiffre_text)
        ]

        rating = (raw_rating and float(raw_rating[0].replace(',', '.'))) or -1
        count = (raw_count and float(raw_count[0].replace(',', '.'))) or -1

        raw_price = [
            chiffre for chiffre_text in
            self.tree.xpath(
                '//*[@data-track-type="wi"]'
                '//*[@itemprop="offers"]'
                '/*[@itemprop="price"]/text()')
            for chiffre in chiffre_regex.findall(chiffre_text)
        ]
        price = (raw_price and float(raw_price[0].replace(',', '.'))) or -1
        foods = [food.strip().replace(',', '') for food in self.tree.xpath(
            '//div[@class="row wine-information-entry"]'
            '//span[@data-item-type="food-pairing"]/text()')]

        region_style = ''.join(self.tree.xpath(
            '//div[@class="row wine-information-entry"]'
            '//a[@data-item-type="wine-style"]/text()'))
        region_style_url = ''.join(self.tree.xpath(
            '//div[@class="row wine-information-entry"]'
            '//a[@data-item-type="wine-style"]/@href'))

        grape_names = self.tree.xpath(
            '//div[@class="row wine-information-entry"]'
            '//a[@data-item-type="grape"]/text()')
        grape_ids = [href2id(href) for href in self.tree.xpath(
            '//div[@class="row wine-information-entry"]'
            '//a[@data-item-type="grape"]/@href')]

        return Win(
            url = url,
            name = name,
            year = year,
            country_name = country_name,
            country_id = country_id,
            region_name = region_name,
            region_id = region_id,
            rating_value = rating,
            rating_count = count,
            price = price,
            foods = foods,
            region_style = region_style,
            region_style_url = region_style_url,
            grape_names = grape_names,
            grape_ids = grape_ids
        )


class GrapTask(FetchTask):
    def parse(self):
        name = ''.join(self.tree.xpath(
            '//h1[@class="grape-name header-mega bold"]/text()'))
        description = ''.join(self.tree.xpath('//p[@class="lead"]//text()'))
        try:
            acidity = float(''.join(self.tree.xpath('//@data-grape-acidity')))
        except Exception:
            acidity = -1
        try:
            color = float(self.tree.xpath('//@data-grape-color'))
        except Exception:
            color = -1
        try:
            body = float(self.tree.xpath('//@data-grape-body'))
        except Exception:
            body = -1
        return Grape(
            url = self.url,
            name = name,
            description = description,
            acidity = acidity,
            color = color,
            body = body
        )
