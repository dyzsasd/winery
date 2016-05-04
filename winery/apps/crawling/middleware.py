from scrapy.exceptions import IgnoreRequest

from winery.apps.crawling.extractors.vivino.models import Win


class DeduplicationMiddleware(object):
    def process_request(self, request, spider):
        if Win.objects(url__exact=request.url):
            print '%s is duplicated' % request.url
            return IgnoreRequest('%s is duplicated' % request.url)
        else:
            print 'new url'
            return None

