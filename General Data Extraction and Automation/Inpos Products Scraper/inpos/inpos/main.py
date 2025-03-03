from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor

from spiders.inposscraper import InposscraperSpider


if __name__ == '__main__':
    crawler_process = CrawlerProcess(get_project_settings())
    print('Start crawler {}'.format(InposscraperSpider.name))
    d = crawler_process.crawl(InposscraperSpider)

    d.addBoth(lambda _: reactor.stop())
    reactor.run()