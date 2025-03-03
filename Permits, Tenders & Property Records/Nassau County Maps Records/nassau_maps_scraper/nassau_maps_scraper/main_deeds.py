from scrapy import cmdline

if __name__ == '__main__':
    # Deeds Scraper
    cmdline.execute('scrapy crawl deeds_spider'.split())
