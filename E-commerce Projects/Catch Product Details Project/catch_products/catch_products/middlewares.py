# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import urllib

from scrapy import signals
from scrapy import Request
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy.utils.response import response_status_message

from urllib.parse import urlencode, unquote, quote

# useful for handling different item types with a single interface
from itemadapter import is_item, ItemAdapter


class CatchProductsSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        a=1
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class CatchProductsDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Check if the spider has a boolean flag for using a proxy
        # if spider.use_proxy and 'scrape.do' not in request.url:
        #     request.meta['proxy'] = spider.proxy
        #     return
        # if spider.use_proxy and 'proxy.scrapeops' not in request.url:
        #     payload = {'api_key': spider.proxy_key, 'url': request.url}
        #     proxy_url = 'https://proxy.scrapeops.io/v1/?' + urlencode(payload)
        #     return request.replace(url=proxy_url)
        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.
        try:
            if response.status != 200 and 'https://www.kogan.com/api/v1/products/?collection=' not in unquote(
                    response.url):
                # Check if it's an HTTPError and the response status is not 200
                # cat = request.meta.get('cat', '')
                url = unquote(response.url).replace('?category=', '?collection=')
                return Request(url=url, callback=spider.parse_category_pagination)
                # return Request(url=quote(url), callback=spider.parse_subcategory_detail)
        except Exception as e:
            self.logger.error(f"Error in process_response: {e}")

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)
