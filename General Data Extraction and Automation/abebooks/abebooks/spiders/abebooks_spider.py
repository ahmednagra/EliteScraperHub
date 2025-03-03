import json
import re
from datetime import datetime
from urllib.parse import urljoin

import scrapy

from ..items import AbebooksItem


class AbeBooksSpider(scrapy.Spider):
    name = 'abe'
    start_urls = ['https://www.abebooks.com/servlet/BookstoreSearch']

    custom_settings = {
        'FEEDS': {
            'Abebooks/%(name)s/%(name)s_%(time)s.json': {
                'format': 'json',
                # 'encoding' : 'utf-8',
                'fields': ['Country', 'seller_name', 'address', 'phone_No', 'join_date', 'rating',
                           'information', 'seller_id', 'seller_url', 'seller_image_url', 'collection']
            }
        }
    }

    def parse(self, response):
        countries = ['AUS', 'ITA', 'USA']
        for country in countries:
            url = f'https://www.abebooks.com/servlet/BookstoreSearch?ph=2&searchtype=1&country={country}&provstate=-1' \
                  f'&currpage=1 '
            print('url :', url)
            yield scrapy.Request(url=url, callback=self.parse_sellers, meta={'country': country})

    def parse_sellers(self, response):
        seller_links = response.css('#search-results-target > li > strong > a::attr(href)').getall()
        print('seller_links', len(seller_links))

        for seller_link in seller_links:
            yield scrapy.Request(
                url=seller_link,
                callback=self.parse_seller_detail,
                meta=response.meta
            )

        next_page_url = response.css('a#bottombar-page-next::attr(href)').get()
        if next_page_url:
            full_next_page_url = urljoin(response.url, next_page_url)
            yield scrapy.Request(
                url=full_next_page_url,
                callback=self.parse_sellers,
                meta=response.meta
            )

    def parse_seller_detail(self, response):
        item = AbebooksItem()

        item['Country'] = response.meta['country']
        item['seller_name'] = response.css('div.seller-location h1::text').get().strip()
        item['address'] = ''.join(part.strip() for part in response.css('p.icon.addy *::text').getall() if part.strip())
        item['phone_No'] = response.css('p.icon.telly::text ').get()
        joindate = response.css('p.date-joined::text').get('')
        item['join_date'] = datetime.strptime(joindate.replace('Joined', '').strip(), '%B %d, %Y').strftime(
            '%d /%m /%Y') if joindate else None
        rating = response.css('.seller-location.indent div a img::attr(alt)').get('')
        item['rating'] = re.sub('-star rating', '', rating) if rating else None
        item['information'] = response.css('.panel-body.seller-content p::text').get()
        seller_id = response.css('link[rel="canonical"]::attr(href)').get('').split('/')[-2]
        item['seller_id'] = seller_id
        item['seller_url'] = response.css('link[rel="canonical"]::attr(href)').get()
        item['seller_image_url'] = response.css('#main > div.seller-info.liquid-static-col > img::attr(src)').get()
        names = response.css('.card-block.text-center  h4::text').getall()
        Links = response.css('div.collection-card a::attr(href)').getall()
        item['collection'] = [{'name': name, 'url': urljoin(response.url, link)}
                              for name, link in zip(names, Links)]

        # Check for "Show more" button and fetch additional records
        show_more_button = response.css('button#load-more-seller')
        print('show_more_button', show_more_button)
        if show_more_button:
            print('before the response. follow')
            offset = 2

            yield response.follow(f'https://www.abebooks.com/collections/curator/{seller_id}?offset={offset}',
                                  self.show_more_records, meta={'item': item, 'offset': offset, 'seller_id': seller_id})
        else:
            yield item

    def show_more_records(self, response):
        item = response.meta['item']
        seller_id = response.meta['seller_id']
        try:
            data = json.loads(response.text)
            resp = data.get('relatedCollections')
        except Exception as error:
            print(f'Error loading JSON data: {error}')
            resp = None

        if resp:
            names = [field.get('curatorName', '') for field in resp]
            links = [field.get('relativeUrl', '') for field in resp]
            more_records = [{'name': name, 'url': urljoin(response.url, link)} for name, link in zip(names, links)]
            item['collection'].extend(more_records)

            offset = int(response.url.split('=')[-1]) + 1
            yield response.follow(f'https://www.abebooks.com/collections/curator/{seller_id}?offset={offset}',
                                  self.show_more_records,
                                  meta={'item': item, 'offset': offset, 'seller_id': item['seller_id']})
        else:
            yield item
