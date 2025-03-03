# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy

from scrapy import Field, Item


class GumtreeBicyclesItem(Item):
    # define the fields for your item here like:
    Name = Field()
    Location = Field()
    Price = Field()
    Date_Posted = Field()
    Image_URL = Field()
    Product_URL = Field()
