# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Item, Field


class TbmsliveDriversItem(Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    driver_name = Field()
    driver_license = Field()
    vehicle_licence_no = Field()
    vehicle_licence_expiry = Field()
    driver_licence_expiry = Field()

    pass

