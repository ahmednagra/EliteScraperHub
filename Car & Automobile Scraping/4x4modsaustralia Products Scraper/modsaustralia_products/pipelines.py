# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter

import scrapy

from scrapy.exceptions import DropItem
from scrapy.pipelines.images import ImagesPipeline


class ModsaustraliaProjPipeline:
    def process_item(self, item, spider):
        return item


class MyImagesPipeline(ImagesPipeline):
    def get_media_requests(self, item, info):
        for index, image_url in enumerate(item["image_urls"]):
            yield scrapy.Request(image_url,
                                 meta={'product_name': item['product_name'], 'image_path': item[f'Img{index + 1}']})

    def file_path(self, request, response=None, info=None, *, item=None):
        return request.meta.get('image_path', '')

    def item_completed(self, results, item, info):
        image_paths = [x["path"] for ok, x in results if ok]

        if not image_paths:
            raise DropItem("Item contains no images")

        adapter = ItemAdapter(item)
        adapter["image_paths"] = image_paths
        return item

