from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from spiders.amazon import AmazonSpider
from spiders.bestbuy import BestbuySpider
from spiders.ebay import EbaySpider
from spiders.newegg import NeweggSpider


def start_sequentially(process: CrawlerProcess, crawlers: list):
    print('start crawler {}'.format(crawlers[0].__name__))
    deferred = process.crawl(crawlers[0])

    if len(crawlers) > 1:
        deferred.addCallback(lambda _: start_sequentially(process, crawlers[1:]))


if __name__ == '__main__':
    spider_crawlers = [AmazonSpider, BestbuySpider, EbaySpider, NeweggSpider ]

    crawler_process = CrawlerProcess(get_project_settings())
    start_sequentially(crawler_process, spider_crawlers)
    crawler_process.start()
