import csv
import glob

from scrapy import Spider, Request
from collections import OrderedDict
from datetime import datetime
from .base import BaseSpider


class Mac4everSpider(BaseSpider):
    name = 'mac4ever'
    start_urls = ['https://www.mac4ever.com/']

    headers = {
        'authority': 'www.mac4ever.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'max-age=0',
        # 'cookie': 'PHPSESSID=8vdorphb93u12g9f3fij9ft0e9; m4tic=RYOr8EMUWMCdUWH3G5w8Ium5At4r78gq9O8KUzgDatHHmXRNhOZN; context=vzd0qen6LhU%2BXr8mL0ORFOMeiTV3ItsMXlCRQ8QQ1BB%2FwYIsJfMR8XHlB79iLKHujKjpzG50TLeCB3x9xoMcgy3RRDuVaLWOFTJhtqHp51m%2BBmAj3GBqBhd2psJMJke3UrZ7Tiuk5Iu%2FC243ZevCdZOvwDs%2FOwufCgcryhpGP7RNqNo%2FEsTmoTIfcEosgQY7X5c7wFimC01CHX9se6o7w%2F5nIiIVe5aanZI8pSmppbezkSMwqk9f4yeX7UUksmjCedkROYAlOTMfcH2%2FP7GR5WpWGeTSeZdjH7FrUollwZaV9RKAWgncLOGwxFYKJ41DigXJJWdJEsb3DWgK7BQgtjJ5wVvwuAbwUTiu4bIEXTQ13D4m8%2FFDbmeS2Zflj0Ijmg%3D%3D; _sharedid=3ebe1201-23d7-43b6-b06c-6e4e9e7ad15a; _sharedid_cst=zix7LPQsHA%3D%3D; cto_bundle=m-JHlF9Mbk1vN1ZybCUyRm1tTDZkSVZodnRhJTJCM0gzcEdwSmpXbzlJZzNqVVFZdVN2MWVZZHBNeUI5TGJZSDZ0b1Zna3VqZ1BKJTJCR0xGYkpCcTdWVHZmaWYwWmtEUmN2eWhab2dieXFjc0RaVzRkUnElMkZXd1p0Mk92SGJHbzVrJTJCV2l0b2JHZkZJTHlpUzJUMDk0OW4lMkJZJTJCTm02QVg3USUzRCUzRA; cto_bidid=e93pZF9FMWFzYmRmeW9qUkFmWkxic3ZpemwlMkJ4MFA4MWRmWEthcDRoNDJKUUdoZ1B3b2tKZEZwekphJTJCWGFFeWxHSFVIOHNqVVdpZlVUYjJzTU9lZmo2Y3pOc05ZamJrNUZsR2pnMzI5UXVxRGF0alElM0Q; _ga_FHQ1XWC6MR=GS1.1.1696840215.1.0.1696840215.0.0.0; _ga=GA1.1.1162733428.1696840216; _gcl_au=1.1.60093659.1696840216; __gads=ID=b4a74f0585b13a28:T=1696840228:RT=1696840228:S=ALNI_Mam6oWxrFN0b6KvEUKrWzu5DPuIDQ; __gpi=UID=00000cb94aa16ecd:T=1696840228:RT=1696840228:S=ALNI_Ma2-VLKlHCccZohy-d51PBHlGzmSw',
        'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    }

    def start_requests(self):
        yield Request(url=self.start_urls[0], headers=self.headers, callback=self.parse)

    def parse(self, response, **kwargs):
        article_url = response.css('.listSummary.container a::attr(href)').getall()
        for url in article_url:
                yield Request(url=response.urljoin(url), callback=self.parse_article)

    def parse_article(self, response):
        item = OrderedDict()
        publish_date_time = response.css('time::attr(datetime)').get('')
        publish_datetime = datetime.strptime(publish_date_time, '%Y-%m-%dT%H:%M:%S%z')
        published_date = publish_datetime.strftime('%Y-%m-%d')

        # date = datetime.now()
        # today_date = date.strftime('%Y-%m-%d').lower().strip()

        if published_date == self.get_today_date():
            item['Title'] = response.css('h1.title ::text').get('')
            item['Summary'] = ''
            item['Image URL'] = response.css('[property="og:image"]::attr(content)').get('')
            item['Description HTML'] = response.css('.content').getall()[:32767]
            item['Published At'] = published_date
            item['Article URL'] = response.url

            self.current_scraped_items.append(item)
