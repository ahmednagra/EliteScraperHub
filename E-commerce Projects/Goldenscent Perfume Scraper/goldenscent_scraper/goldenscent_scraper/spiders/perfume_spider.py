import os
import json
from datetime import datetime
from .perfume_seprate_info import PerfumeSpider

"""
THIS SPIDER IS SCRAPING THE INFORMATION SECTION FIELDS IN SINGLE COLUMNS. 
THE REST OF THE WORKING IS THE SAME 
"""


class PerfumeSpiderSpider(PerfumeSpider):
    name = 'perfume_spider'
    current_dt = datetime.now().strftime("%Y-%m-%d %H%M%S")

    custom_settings = {
        'CONCURRENT_REQUESTS': 3,
        'DOWNLOAD_DELAY': 1,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 10,

        'FEED_EXPORTERS': {
            'xlsx': 'scrapy_xlsx.XlsxItemExporter',
        },

        'FEEDS': {
            f'output/GoldenScent Perfume Details Combine_Info  {current_dt}.xlsx': {
                'format': 'xlsx',
                'fields': ['Title', 'Brand', 'Perfume Id', 'Rating',
                           'Votes Count', 'Sku', 'Size', 'Price', 'Special Price',
                           'Stock Status', 'Ingredients', 'Images', 'Delivery Time',
                           'URL', 'Information', 'Description'],
            }
        },
    }

