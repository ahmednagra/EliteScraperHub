from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from spiders.indeed_scraper import IndeedScraperSpider


if __name__ == '__main__':
    settings = get_project_settings()
    process = CrawlerProcess(settings=settings)

    process.crawl(IndeedScraperSpider)

    print('start crawler TabelogspiderSpider')

    process.start()  # the script will block here until the crawling is finished


