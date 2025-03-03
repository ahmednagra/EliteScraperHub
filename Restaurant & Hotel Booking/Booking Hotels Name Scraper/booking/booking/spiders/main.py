from scrapy.crawler import CrawlerProcess

try:
    from nocowanie_hotels import NocowanieHomeSpider
    from booking_hotels import HotelsNamesSpider
except:
    from .nocowanie_hotels import NocowanieHomeSpider
    from .booking_hotels import HotelsNamesSpider


# Create a list of spider classes
spiders = [NocowanieHomeSpider, HotelsNamesSpider]
# spiders = [NocowanieHomeSpider]

# Create a CrawlerProcess
process = CrawlerProcess()

# Add each spider to the process
for spider in spiders:
    process.crawl(spider)

# Start the process
process.start()
