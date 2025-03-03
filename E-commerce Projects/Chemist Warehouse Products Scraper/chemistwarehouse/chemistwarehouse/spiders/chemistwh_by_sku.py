import glob

from scrapy import Request

from .chemistwh_by_category import ChemistScraperSpider


class ChemistSKuSpider(ChemistScraperSpider):
    name = 'chemist_sku'
    start_urls = ['https://www.chemistwarehouse.com.au/']

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.skus = self.read_skus()

    def start_requests(self):
        for sku in self.skus:
            url = f'https://www.chemistwarehouse.com.au/buy/{sku}/'
            yield Request(url=url, callback=self.parse_product_detail)

    def read_skus(self):
        file_name = ''.join(glob.glob('input/SKUs.txt'))
        try:
            with open(file_name, 'r') as file:
                lines = file.readlines()

            # Strip newline characters and whitespace from each line
            lines = [line.strip() for line in lines]
            return lines
        except:
            return []
