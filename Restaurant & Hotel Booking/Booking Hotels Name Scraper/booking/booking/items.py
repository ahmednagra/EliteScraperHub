# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy import Item, Field


class BookingItem(Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    Name = Field()
    Actual_Price = Field()
    Discounted_Price = Field()
    Date_start = Field()
    Date_end = Field()
    Guests_adult = Field()
    Guest_children = Field()
    City = Field()

    pass
