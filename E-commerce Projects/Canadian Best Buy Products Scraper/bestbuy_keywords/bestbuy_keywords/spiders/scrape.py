import logging
from scrapy.crawler import CrawlerProcess
from individuals_pages import SitemapsSpider


class Command():
    help = 'Scrape data'

    def handle(self, *args, **kwargs):
        logging.getLogger('scrapy').propagate = False
        process = CrawlerProcess()
        process.crawl(SitemapsSpider)  # which spider need to run
        print('process from scrape.py:', process)
        process.start()
