from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor

from spiders.weedmaps import WeedmapsspiderSpider


if __name__ == '__main__':
    crawler_process = CrawlerProcess(get_project_settings())
    print('Start crawler {}'.format(WeedmapsspiderSpider.name))
    d = crawler_process.crawl(WeedmapsspiderSpider)

    d.addBoth(lambda _: reactor.stop())
    reactor.run()