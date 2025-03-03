from datetime import datetime
from collections import OrderedDict
from urllib.parse import urljoin
from scrapy import Spider, Request


class RacingpostSpider(Spider):
    name = "racingpost"
    base_url = 'www.racingpost.com'
    start_urls = ["https://www.racingpost.com/racecards/"]

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'no-cache',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    }

    custom_settings = {
        'FEEDS': {
            f'output/Racing Post {datetime.now().strftime("%d%m%Y%H%M%S")}.csv': {
                'format': 'csv',
                'fields': ['DATE', 'VENUE', 'TIME', 'FAVOURITE'],
            }
        }
    }

    def parse(self, response, **kwargs):
        self.logger.error(f'Error occurred in parse_venue_matches method')
        try:
            venues_urls = response.css('.RC-accordion section:not(:contains("ABANDONED")) .RC-meetingList__showAll::attr(href)').getall()
            for venue_url in venues_urls:
                url = urljoin(response.url, venue_url)
                yield Request(url=url, callback=self.parse_venue_matches, headers=self.headers)
        except Exception as e:
            self.logger.error(f'Error occurred in parse method: {str(e)}')

    def parse_venue_matches(self, response):
        try:
            venue = response.css('.RC-meetingDay__titleName a::text').get('').strip()
            date = response.css('.RC-meetingDay__titleDate::text').get('').strip()

            matches_selector = response.css('.RC-meetingDay__race')
            for match in matches_selector:
                item = OrderedDict()
                item['VENUE'] = venue
                item['DATE'] = date
                item['TIME'] = match.css('.RC-meetingDay__raceTime::text').get('').strip()
                item['FAVOURITE'] = self.get_favroite(match)

                yield item
        except Exception as e:
            self.logger.error(f'Error occurred in parse_venue_matches method: {str(e)}')

    def get_favroite(self, match):
        selectors_text = match.css('.RC-raceVerdict__content b ::text').getall()
        for text in selectors_text:
            if sum(1 for char in text if char.isupper()) > 2:  # Check if the verdict has more than two uppercase letters
                return text
        return ''
