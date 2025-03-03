from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from spiders.tabelogspider import TabelogspiderSpider


if __name__ == '__main__':
    settings = get_project_settings()
    process = CrawlerProcess(settings=settings)

    process.crawl(TabelogspiderSpider)

    print('start crawler TabelogspiderSpider')

    process.start()  # the script will block here until the crawling is finished


