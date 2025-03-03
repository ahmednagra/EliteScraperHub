from scrapy import Spider


class ConcavebtSpider(Spider):
    name = "concavebt"
    allowed_domains = ["concavebt.com"]
    start_urls = ['https://concavebt.com/top-100-product-placement-brands-in-2022-movies/']

    def parse(self, response):
        first_ten = [name.split(' ', 1)[1] for name in response.css('#tablepress-38 center::text').getall()]
        eleven_to_fifty = response.css('#tablepress-39 center::text').re(r'#\d+\s*(.+)')
        fifty_to_hundred = response.css('#tablepress-40 center::text').re(r'#\d+\s*(.+)')

        with open('100brands.txt', 'w') as file:
            for name in first_ten:
                file.write(name + "\n")

            for name in eleven_to_fifty:
                file.write(name + "\n")

            for name in fifty_to_hundred:
                file.write(name + "\n")
