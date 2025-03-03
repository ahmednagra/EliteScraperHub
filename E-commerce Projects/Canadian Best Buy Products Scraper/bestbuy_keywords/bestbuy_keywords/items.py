# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html


from scrapy import Field, Item


class BestbuyProductsItem(Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    keyword = Field()
    Title = Field()
    Model = Field()
    Sku = Field()
    Discounted_Price = Field()
    Actual_Price = Field()
    Discount_Amount = Field()
    Status = Field()
    Image = Field()
    URL = Field()
    Description = Field()

    pass
