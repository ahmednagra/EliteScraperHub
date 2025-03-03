# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class BalaanItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    product_Id = scrapy.Field()
    Title = scrapy.Field()
    Price = scrapy.Field()
    address = scrapy.Field()
    Old_Price = scrapy.Field()
    Brand = scrapy.Field()
    SKU = scrapy.Field()
    Color = scrapy.Field()
    Size = scrapy.Field()
    Stock_Status = scrapy.Field()
    Category = scrapy.Field()
    Image_URL = scrapy.Field()
    Product_URL = scrapy.Field()
    pass
