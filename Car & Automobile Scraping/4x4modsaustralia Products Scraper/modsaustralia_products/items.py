# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class ModsaustraliaProjItem(scrapy.Item):
    # define the fields for your item here like:
    product_name = scrapy.Field()
    SKU = scrapy.Field()
    Make = scrapy.Field()
    Model = scrapy.Field()
    Year = scrapy.Field()
    Price = scrapy.Field()
    Category = scrapy.Field()
    Availability = scrapy.Field()
    image_urls = scrapy.Field()
    images = scrapy.Field()
    Product_URL = scrapy.Field()
    Description = scrapy.Field()
    Specifications = scrapy.Field()
    image_results = scrapy.Field()
    file_paths = scrapy.Field()
    image_paths = scrapy.Field()

    # # Add the new image fields
    Img1 = scrapy.Field()
    Img2 = scrapy.Field()
    Img3 = scrapy.Field()
    Img4 = scrapy.Field()
    Img5 = scrapy.Field()

    pass
