import scrapy

from ebook_scrapper.items import BookItem


class EbookSpider(scrapy.Spider):
    name ="ebook"
    start_urls = [
        'http://books.toscrape.com/catalogue/category/books_1/index.html'  
        ]
    
    custom_settings = {
    'FEED_EXPORT_ENCODING': 'utf-8',
    'FEEDS': {
        'data/%(name)s/%(name)s_%(time)s.csv': {
            'format': 'csv',
            'fields': ['book_name', 'Category', 'book_rating', 'book_description', 'book_price', 'book_stock_status', 
                                 'book_upc', 'book_product_type', 'book_price_excl_tax', 'book_price_incl_tax', 'book_tax',
                                   'book_reviews', 'book_img_url', 'book_url']
                    }
                }
            }
                

    def parse(self, response):
        print('start parse function')
        category_links = response.css('ul.nav.nav-list li ul li a::attr(href)').getall()
        category_names = [name.strip().replace('\n', '') for name in response.css('ul.nav.nav-list li ul li a::text').getall()]

        for category_link, category_name in zip(category_links, category_names):
            url = response.urljoin(category_link)
            yield scrapy.Request(url, callback=self.parse_category, meta={'category_name': category_name})
    
    def parse_category(self, response):
        book_links = response.css('h3 a::attr(href)').getall()
        book_names = response.css('h3 a::text').getall()
        
        for book_link, book_name in zip(book_links, book_names):
            url = response.urljoin(book_link)
            yield scrapy.Request(url, callback=self.parse_book, meta=response.meta)
            
        # Check if there is a next page of books in the category and send a request if there is
        next_page_url = response.css('li.next a::attr(href)').get()
        if next_page_url:
            next_page_url = response.urljoin(next_page_url)
            yield scrapy.Request(next_page_url, callback=self.parse_category, meta=response.meta)

    def book_value(self, response, heading):
        return response.css(f"th:contains('{heading}') + td::text").get().strip().replace('£','')        

    def parse_book(self, response):
        item = BookItem()

        item['book_name'] = response.css('div.product_main h1::text').get()
        item['Category'] = response.css('ul.breadcrumb li:nth-last-child(2) a::text').get()
        item['book_rating'] = response.css('p.star-rating::attr(class)').re_first('star-rating (\w+)')
        item['book_description'] = response.css('#product_description + p::text').get()
        item['book_price'] = response.css('p.price_color::text').get().strip().replace('£', '')
        item['book_stock_status'] = (response.css('p.availability::text').re_first('\n(.*)\s*\(').strip()
                            if response.css('p.availability::text').get() else None)
        item['book_upc'] = self.book_value(response, "UPC")
        item['book_product_type'] = self.book_value(response, "Product Type")
        item['book_price_excl_tax'] = self.book_value(response, "Price (excl. tax)")
        item['book_price_incl_tax'] = self.book_value(response, "Price (incl. tax)")
        item['book_tax'] = self.book_value(response, "Tax")
        item['book_reviews'] = self.book_value(response, "Number of reviews")
        item['book_img_url'] = response.urljoin(response.css('div.item.active img::attr(src)').get())
        item['book_url'] = response.url

        # Yield the item to the pipeline
        yield item