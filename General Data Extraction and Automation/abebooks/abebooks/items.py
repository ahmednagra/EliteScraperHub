# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class AbebooksItem(scrapy.Item):
    # define the fields for your item here like:
    seller_name = scrapy.Field()
    address = scrapy.Field()
    Country = scrapy.Field()
    phone_No = scrapy.Field()
    rating = scrapy.Field()
    join_date = scrapy.Field()
    information = scrapy.Field()
    seller_id = scrapy.Field()
    seller_url = scrapy.Field()
    seller_image_url = scrapy.Field()
    collection = scrapy.Field()
    pass
