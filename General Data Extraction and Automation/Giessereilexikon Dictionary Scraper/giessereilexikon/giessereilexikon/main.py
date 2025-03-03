from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from spiders.giessereilexikonspider import GiessereilexikonspiderSpider


if __name__ == '__main__':
    settings = get_project_settings()
    process = CrawlerProcess(settings=settings)

    process.crawl(GiessereilexikonspiderSpider)

    print('start crawler GiessereilexikonspiderSpider')

    process.start()  # the script will block here until the crawling is finished


