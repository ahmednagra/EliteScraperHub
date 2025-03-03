from datetime import datetime
from urllib.parse import urlencode
from collections import OrderedDict
from scrapy import Request, Spider


class FragranticaSpider(Spider):
    name = 'fragrantica'
    base_url = 'https://www.fragrantica.com'
    start_urls = ['https://www.fragrantica.com/search/']

    custom_settings = {
        # 'CONCURRENT_REQUESTS': 1,
        'FEEDS': {
            f'output/Fragrantica Perfume Details {datetime.now().strftime("%d%m%Y%H%M")}.csv': {
                'format': 'csv',
                'fields': ['URL', 'Title', 'Brand', 'Rating', 'Votes Count', 'Main Accords', 'Short Description',
                           'Long Description', 'Pros', 'Cons', 'Top Notes', 'Middle Notes', 'Base Notes', 'Perfumers',
                           'Images'],
            }
        },

    }

    headers = {
        'sec-ch-ua': '"Chromium";v="116", "Not)A;Brand";v="24", "Google Chrome";v="116"',
        'sec-ch-ua-platform': '"Windows"',
        'Referer': 'https://www.fragrantica.com/',
        'sec-ch-ua-mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
        'content-type': 'application/x-www-form-urlencoded',
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.language_character = 'EN'
        self.headers['Referer'] = self.base_url

    def start_requests(self):
        page_no = 0
        gender_filters = ['unisex', 'female', 'male']

        for year in range(1920, 2025):  # Iterate over years from 1920 to 2024
            for gender_filter in gender_filters:
                data = self.get_form_data(year, page_no, gender_filter)

                yield Request(
                    url='https://fgvi612dfz-3.algolianet.com/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(4.19.1)%3B%20Browser%20(lite)%3B%20instantsearch.js%20(4.56.8)%3B%20Vue%20(2.7.14)%3B%20Vue%20InstantSearch%20(4.10.8)%3B%20JS%20Helper%20(3.14.0)&x-algolia-api-key=YjVlZTU3MWM4YTkwYTBhZmU5MjRlZTc4MGJjMTBmMDI0OTA0YWI0NGRmNjdkZjMwZTA3YWYxMWQ1OTI3OGNjNHZhbGlkVW50aWw9MTY5NTAxNzYwMQ%3D%3D&x-algolia-application-id=FGVI612DFZ',
                    headers=self.headers,
                    method='POST',
                    body=data,
                    meta={'gender_filter': gender_filter, 'year': year, 'page_no': page_no},
                    callback=self.parse_products,
                )

    def parse_products(self, response):
        try:
            json_data = response.json().get('results', [{}])[0]
        except Exception as e:
            print(f"An error occurred: {e}")
            return

        next_page = json_data.get('nbPages', 0)
        year = response.meta.get('year', 0)
        gender_filter = response.meta.get('gender_filter', '')
        for page_no in range(0, next_page + 1):
            data = self.get_form_data(year, page_no, gender_filter)

            yield Request(
                url='https://fgvi612dfz-3.algolianet.com/1/indexes/*/queries?x-algolia-agent=Algolia%20for%20JavaScript%20(4.19.1)%3B%20Browser%20(lite)%3B%20instantsearch.js%20(4.56.8)%3B%20Vue%20(2.7.14)%3B%20Vue%20InstantSearch%20(4.10.8)%3B%20JS%20Helper%20(3.14.0)&x-algolia-api-key=YjVlZTU3MWM4YTkwYTBhZmU5MjRlZTc4MGJjMTBmMDI0OTA0YWI0NGRmNjdkZjMwZTA3YWYxMWQ1OTI3OGNjNHZhbGlkVW50aWw9MTY5NTAxNzYwMQ%3D%3D&x-algolia-application-id=FGVI612DFZ',
                headers=self.headers,
                method='POST',
                body=data,
                callback=self.pagination,
                dont_filter=True
            )

    def pagination(self, response):
        perfume_urls = self.get_perfume_urls(response)
        for url in perfume_urls:
            yield Request(url=self.get_scrapeops_url(url), callback=self.parse_product_detail, meta={'url': url})

    def get_form_data(self, year, page_no, gender_filter):
        data = f'''
                    {{
                      "requests": [
                        {{
                          "indexName": "fragrantica_perfumes",
                          "params": "attributesToRetrieve=%5B%22naslov%22%2C%22dizajner%22%2C%22godina%22%2C%22url.{self.language_character}%22%2C%22thumbnail%22%5D&facetFilters=%5B%5B%22spol%3A{gender_filter}%22%5D%5D&facets=%5B%22designer_meta.category%22%2C%22designer_meta.country%22%2C%22designer_meta.main_activity%22%2C%22designer_meta.parent_company%22%2C%22dizajner%22%2C%22godina%22%2C%22ingredients.EN%22%2C%22nosevi%22%2C%22osobine.EN%22%2C%22rating_rounded%22%2C%22spol%22%5D&highlightPostTag=__%2Fais-highlight__&highlightPreTag=__ais-highlight__&hitsPerPage=80&maxValuesPerFacet=10&numericFilters=%5B%22godina>={year}%22%2C%22godina<={year}%22%5D&page={page_no}&query=&tagFilters="
                        }},
                        {{
                          "indexName": "fragrantica_perfumes",
                          "params": "analytics=false&attributesToRetrieve=%5B%22naslov%22%2C%22dizajner%22%2C%22godina%22%2C%22url.{self.language_character}%22%2C%22thumbnail%22%5D&clickAnalytics=false&facetFilters=%5B%5B%22spol%3A{gender_filter}%22%5D%5D&facets=godina&highlightPostTag=__%2Fais-highlight__&highlightPreTag=__ais-highlight__&hitsPerPage=0&maxValuesPerFacet=10&page=0&query="
                        }},
                        {{
                          "indexName": "fragrantica_perfumes",
                          "params": "analytics=false&attributesToRetrieve=%5B%22naslov%22%2C%22dizajner%22%2C%22godina%22%2C%22url.{self.language_character}%22%2C%22thumbnail%22%5D&clickAnalytics=false&facets=spol&highlightPostTag=__%2Fais-highlight__&highlightPreTag=__ais-highlight__&hitsPerPage=0&maxValuesPerFacet=10&numericFilters=%5B%22godina>={year}%22%2C%22godina<={year}%22%5D&page=0&query="
                        }}
                      ]
                    }}
                    '''

        return data

    def parse_product_detail(self, response):
        item = OrderedDict()

        item['URL'] = response.meta.get('url', '')
        item['Title'] = response.css('h1[itemprop="name"]::text').get('')
        item['Brand'] = response.css('[itemprop="brand"] span::text').get('')
        item['Rating'] = response.css('[itemprop="ratingValue"] ::text').get('')
        item['Votes Count'] = response.css('[itemprop="ratingCount"]::attr(content)').get('')
        item['Main Accords'] = ', '.join(response.css('.accord-bar::text').getall()) or []
        item['Short Description'] = ''.join(
            response.xpath('//div[@itemprop="description"]/p[1]').css('::text').getall()) or []
        item['Long Description'] = ''.join(response.css('.fragrantica-blockquote p::text').getall()) or []
        item['Pros'] = '\n'.join(
            [x.strip() for x in response.css('.small-6:contains(Pros) .small-12::text ').getall() if x.strip()])
        item['Cons'] = '\n'.join(
            [x.strip() for x in response.css('.small-6:contains(Cons) .small-12::text ').getall() if x.strip()])
        item['Top Notes'] = ', '.join(response.css('[notes="top"] div::text').getall()) or []
        item['Middle Notes'] = ', '.join(response.css('[notes="middle"] div::text').getall()) or []
        item['Base Notes'] = ', '.join(response.css('[notes="base"] div::text').getall()) or []
        item['Perfumers'] = ', '.join(
            response.css('.small-12:contains("Perfumer") .medium-up-2 a::text').getall()) or response.css(
            '.perfumer-avatar + a::text').get('')
        item['Images'] = response.css('.small-6.text-center img[itemprop="image"]::attr(src)').get('')

        yield item

    def get_scrapeops_url(self, url):
        API_KEY = '69407ad1-67b8-4a4f-8083-137167f3b908'
        payload = {'api_key': API_KEY, 'url': url}
        proxy_url = 'https://proxy.scrapeops.io/v1/?' + urlencode(payload)
        return proxy_url

    def get_perfume_urls(self, response):
        try:
            json_data = response.json().get('results', [{}])[0]
        except Exception as e:
            print(f"An error occurred: {e}")
            return

        try:
            perfume_urls = [row.get('url', {}).get(self.language_character)[0] for row in json_data.get('hits')]
        except Exception as e:
            print(f"An error occurred: {e}")
            return

        return perfume_urls
