# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.ht
from scrapy import Item, Field


class AmazonScraperItem(Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    Product_URL = Field()
    Brand_Name = Field()
    Product_Name = Field()
    Regular_Price = Field()
    Special_Price = Field()
    Short_Description = Field()
    Long_Description = Field()
    Product_Information = Field()
    Directions = Field()
    Ingredients = Field()
    SKU = Field()
    ASIN = Field()
    Barcode = Field()
    Image_URLs = Field()

    pass
