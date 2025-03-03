from scrapy import cmdline

if __name__ == '__main__':
    # Map Scraper
    cmdline.execute('scrapy crawl nassau_spider'.split())