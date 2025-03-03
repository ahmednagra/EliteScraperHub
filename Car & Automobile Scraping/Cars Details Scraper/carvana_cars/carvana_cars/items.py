# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Field


class CarvanaCarsItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    sku = Field()
    model = Field()
    color = Field()
    year = Field()
    image = Field()
    make = Field()
    description = Field()
    condition = Field()
    url = Field()
    mileage = Field()
    price = Field()
    location = Field()
    Vin_number = Field()

    pass
