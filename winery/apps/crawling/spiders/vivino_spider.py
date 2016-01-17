from scrapy.spiders import SitemapSpider

from winery.apps.crawling.items import VivinoItem


class VivinoSpider(SitemapSpider):
    name = 'VivinoSpider'
    sitemap_urls = ['https://www.vivino.com/sitemap.xml']
    sitemap_follow = ['/sitemap/[^/]+\.xml\.gz']

    sitemap_rules = [
        ('/wine-countries/', 'parse_item'),
        ('/wine-regions/', 'parse_item'),
        ('/wineries/', 'parse_item'),
        ('/grapes/', 'parse_item'),
    ]

    def parse_item(self, response):
        item = VivinoItem(
            url=response.url,
            content=response.body
        )
        return item

