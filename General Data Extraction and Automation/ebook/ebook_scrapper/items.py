# # Define here the models for your scraped items
# #
# # See documentation in:
# # https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class BookItem(scrapy.Item):
    book_name = scrapy.Field()
    Category = scrapy.Field()
    book_rating = scrapy.Field()
    book_description = scrapy.Field()
    book_price = scrapy.Field()
    book_stock_status = scrapy.Field()
    book_upc = scrapy.Field()
    book_product_type = scrapy.Field()
    book_price_excl_tax = scrapy.Field()
    book_price_incl_tax = scrapy.Field()
    book_tax = scrapy.Field()
    book_reviews = scrapy.Field()
    book_img_url = scrapy.Field()
    book_url = scrapy.Field()