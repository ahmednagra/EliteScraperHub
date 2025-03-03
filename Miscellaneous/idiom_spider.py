import os

from scrapy import Spider, Request


class IdiomSpiderSpider(Spider):
    name = "idiom_spider"
    start_urls = ["https://www.theidioms.com"]

    counter = 0

    custom_settings = {
        'CONCURRENT_REQUESTS': 8,
    }

    headers = {
        'authority': 'www.theidioms.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'max-age=0',
        # 'cookie': '__gads=ID=b0ecdec6ca74e9b9-2262761bc7e000e8:T=1685103924:RT=1685103924:S=ALNI_MavNumifqMajfA2525bGtOVjDxsWA; __gpi=UID=00000c35fd7e74b3:T=1685103924:RT=1685103924:S=ALNI_MbW5ouATm8k_p16_ZA35LEPWHUtOA',
        'sec-ch-ua': '"Google Chrome";v="113", "Chromium";v="113", "Not-A.Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    }

    cookies = {
        '__gads': 'ID=b0ecdec6ca74e9b9-2262761bc7e000e8:T=1685103924:RT=1685103924:S=ALNI_MavNumifqMajfA2525bGtOVjDxsWA',
        '__gpi': 'UID=00000c35fd7e74b3:T=1685103924:RT=1685103924:S=ALNI_MbW5ouATm8k_p16_ZA35LEPWHUtOA',
    }

    def start_requests(self):
        url = 'https://www.theidioms.com/list/alphabetical/'

        yield Request(url=url, headers=self.headers, cookies=self.cookies, callback=self.parse)

    def parse(self, response):
        all_letters_hrefs = response.css('.article a::attr(href)').getall()

        for href in all_letters_hrefs:
            self.counter += 1
            yield Request(url=href, headers=self.headers, cookies=self.cookies, callback=self.word_idioms,
                          )

    def word_idioms(self, response):
        hrefs = response.css('.idiom strong + ::attr(href)').getall()
        for href in hrefs:
            self.counter += 1
            yield Request(url=href, headers=self.headers, cookies=self.cookies, callback=self.idiom,
                          )

        next_page = response.css('.nxt a::attr(href)').get('')

        if next_page:
            yield Request(url=next_page, callback=self.word_idioms)

    def idiom(self, response):
        folder = 'web_pages'
        if not os.path.exists(folder):
            os.makedirs(folder)

        filename = os.path.join(folder, f'{response.url.split("/")[-2]}.html')
        with open(filename, 'wb') as f:
            f.write(response.body)

    def closed(self, reason):
        self.logger.info('Total requests made: %s', self.counter)
