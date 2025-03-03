# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import logging
import scrapy
from scrapy import Request
from scrapy.pipelines.images import ImagesPipeline
from scrapy.exceptions import DropItem


class PccomponentesPipeline:
    def process_item(self, item, spider):
        return item


class customimagePipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        images = item.get('Images URLs')
        ean = item.get('EAN', '').replace("'", "")

        for image_index, image_url in enumerate(images):
            # image_url = 'https://img.pccomponentes.com/articles/14/149429/10-15-0704.jpg'
            image_name = f'{ean}_image{image_index+1}.jpg'
            yield Request(url=image_url, meta={'image_name': image_name})

    def file_path(self, request, response=None, info=None, *, item=None):
        return request.meta.get('image_name')
