from datetime import datetime
from collections import OrderedDict

from scrapy import Spider, Request


class GiessereilexikonspiderSpider(Spider):
    name = "giessereilexikon"
    allowed_domains = 'https://www.giessereilexikon.com'
    start_urls = ['https://www.giessereilexikon.com/en/foundry-lexicon/']

    custom_settings = {
        'CONCURRENT_REQUESTS': 8,
        'FEED_EXPORTERS': {'xlsx': 'scrapy_xlsx.XlsxItemExporter'},
        'FEED_URI': f'output/Giessereilexikon Words scraper.xlsx',
        'FEED_FORMAT': 'xlsx'
    }

    def parse(self, response):
        self.write_logs("Scraping is started", mode='w')

        word_urls = response.css('.tx_d3ency_list a::attr(href)').getall()
        for word in word_urls:
            yield Request(url=response.urljoin(word), callback=self.parse_word_EN, dont_filter=True)

    def parse_word_EN(self, response):
        english_word = self.get_word(response)
        english_explanation = self.get_description(response)

        if not english_word:
            self.write_logs(f"Against this Word No Record Exist. Word Url is : {response.url}")
            return

        de_url = response.css('.langnavi a::attr(href)').get()
        en_url = response.url

        yield Request(url=response.urljoin(de_url), callback=self.parse_word_DE,
                      meta={'english_word': english_word,
                            'english_explanation': english_explanation,
                            'en_url': en_url},
                      dont_filter=True)

    def parse_word_DE(self, response):
        item = OrderedDict()

        item['English Word'] = response.meta.get('english_word', '')
        item['English Explanation'] = response.meta.get('english_explanation', '')
        item['German Word'] = self.get_word(response)
        item['German Explanation'] = self.get_description(response)
        item['English URL'] = response.meta.get('en_url', '')
        item['German URL'] = response.url

        yield item

    def get_description(self, response):
        description = '\n\n'.join([''.join(tag.css('::text').getall()) if not tag.css('* li') else '- ' + '\n- '.join(
            [''.join(li.css('::text').getall()) for li in tag.css('* li')]) for tag in
                                   response.xpath('//div[@class="tx_d3ency-text-detail"]/*')]).strip()

        return description[:32767]

    def get_word(self, response):
        return response.css('.tx_d3ency-show h2::text').get('')

    def write_logs(self, message, mode='a'):
        with open("logs.txt", mode=mode, encoding='utf-8') as txt_file:
            txt_file.write(f"{datetime.now()} -> {message}\n")
