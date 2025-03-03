import csv
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from spiders.alternate import AlternateScraperSpider
from spiders.alza import AlzaScraperSpider
from spiders.bikemarket24 import BikeMarketScraperSpider
from spiders.fahrrad import FahrradScraperSpider
from spiders.fahrrad_xxl import FahrradxxlScraperSpider
from spiders.flaconi import FlaconiScraperSpider
from spiders.ibood import IboodScraperSpider
from spiders.manomano import ManomanoScraperSpider
from spiders.mediamarkt import MediamarketScraperSpider
from spiders.muller import MullerScraperSpider
from spiders.radwelt_shop import RadweltScraperSpider
from spiders.telekom import TelekomScraperSpider
from spiders.thalia import ThaliaScraperSpider
from spiders.voelkner import VoelknerScraperSpider

from twisted.internet import defer
from twisted.internet import reactor


def start_sequentially(process: CrawlerProcess, crawlers: list):
    deferreds = []
    for crawler in crawlers:
        print('start crawler {}'.format(crawler.__name__))
        deferred = process.crawl(crawler)
        deferreds.append(deferred)

    return defer.DeferredList(deferreds)


def read_input_file():
    input_file = 'input/scraper_status.csv'

    with open(input_file, mode='r', encoding='utf8') as input_file:
        return list(csv.DictReader(input_file))


if __name__ == '__main__':

    csv_rows = read_input_file()
    # Dont run and process those spiders which are not set to True in the csv file
    dont_run_crawlers = [row['SpiderName'].strip() for row in csv_rows if 'true' not in row.get('Process', '').lower()]

    spider_crawlers = [AlternateScraperSpider, BikeMarketScraperSpider, FahrradScraperSpider,
                       FahrradxxlScraperSpider,
                       FlaconiScraperSpider, IboodScraperSpider,
                       MullerScraperSpider, RadweltScraperSpider, TelekomScraperSpider,
                       VoelknerScraperSpider, AlzaScraperSpider, ManomanoScraperSpider,
                       MediamarketScraperSpider, ThaliaScraperSpider
                       ]

    crawlers = [crawler for crawler in spider_crawlers if crawler.name not in dont_run_crawlers]

    crawler_process = CrawlerProcess(get_project_settings())
    d = start_sequentially(crawler_process, crawlers)

    d.addBoth(lambda _: reactor.stop())
    reactor.run()
