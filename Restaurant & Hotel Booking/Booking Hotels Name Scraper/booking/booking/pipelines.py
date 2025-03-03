# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import os
from datetime import datetime

from itemadapter import ItemAdapter

from openpyxl import Workbook


# class BookingPipeline:
#     def process_item(self, item, spider):
#         return item
class BookingPipeline:
    def __init__(self):
        self.wb = Workbook()

    def open_spider(self, spider):
        self.sheet = self.wb.create_sheet(title=spider.name)
        self.headers_written = False

    def close_spider(self, spider):
        # Create the directory if it doesn't exist
        output_dir = 'booking/output/'
        os.makedirs(output_dir, exist_ok=True)

        file_name = f'{output_dir}Booking Names_Price {datetime.now().strftime("%d%m%Y")}.xlsx'
        self.wb.save(file_name)

    def process_item(self, item, spider):
        if not self.headers_written:
            headers = list(item.keys())
            self.sheet.append(headers)
            self.headers_written = True

        row = list(item.values())
        self.sheet.append(row)

        return item
