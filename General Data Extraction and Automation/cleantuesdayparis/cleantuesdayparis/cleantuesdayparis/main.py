from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from twisted.internet import defer
from twisted.internet import reactor

def start_sequentially(crawler_process, crawlers):
    # Create a deferred chain to run the crawlers sequentially
    d = defer.Deferred()
    chain = d
    for crawler in crawlers:
        print(f'{crawler} spider is started')
        chain.addCallback(lambda _, c=crawler: crawl(crawler_process, c))

    # Fire the first deferred to start the chain
    d.callback(None)
    return d


def crawl(crawler_process, spider):
    d = crawler_process.crawl(spider)
    return d


if __name__ == '__main__':
    spider_names = ["cleantuesdayparis"]  # Use the spider name, not the spider class
    crawlers = [crawler for crawler in spider_names]

    crawler_process = CrawlerProcess(get_project_settings())
    d = start_sequentially(crawler_process, crawlers)

    d.addBoth(lambda _: reactor.stop())
    reactor.run()
