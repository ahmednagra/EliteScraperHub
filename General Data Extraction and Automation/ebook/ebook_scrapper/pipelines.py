# # Define your item pipelines here
# #
# # Don't forget to add your pipeline to the ITEM_PIPELINES setting
# # See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
# import csv
# from itertools import count

# #mongodb
# from pymongo import MongoClient


class EbookScrapperPipeline:
    pass
#     def __init__(self):
#         self.filename = 'books.csv'
#         self.fieldnames = ['book_directory', 'book_name', 'book_url', 
#                            'book_img_url', 'book_rating', 'book_description',
#                              'book_price', 'book_stock_status', 'book_upc', 
#                              'book_product_type', 'book_price_excl_tax', 
#                              'book_price_incl_tax', 'book_tax', 'book_reviews']


#     def open_spider(self, spider):
#         with open(self.filename, 'w', newline='') as csv_file:
#             writer = csv.DictWriter(csv_file, fieldnames=self.fieldnames)
#             writer.writeheader()

#     def process_item(self, item, spider):
#         item_dict = dict(item)
#         with open(self.filename, 'r', newline='') as csvfile:
#             reader = csv.DictReader(csvfile)
#             rows = sorted(reader, key=lambda row: row['book_directory'])
        
#         with open(self.filename, 'w', newline='') as csvfile:
#             writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
#             writer.writeheader()
#             for row in rows:
#                 writer.writerow(row)
#             writer.writerow(item_dict)
    
#         return item

#     def close_spider(self, spider):
#         self.file.close()   
