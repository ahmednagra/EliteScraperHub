from ..items import HomesPropertiesItem

from .basespider import BaseSpider


class HomesSaleSpider(BaseSpider):
    name = "homes_sale"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.prop_type = 1
        self.location_property_type = 'property_type=1,2,260,64'
        self.homes_url = self.all_homes_url
        self.next_page = self.nxt_page
        self.next_page_url = self.nxt_page_url

    def home_detail(self, response):

        dictitems = self.same_selectors(response)
        item = HomesPropertiesItem()
        item.update(dictitems)

        # Non Common
        item['Price'] = str(float(response.css('#price::text').get('').replace('$', '').replace(',', '')))
        item['Baths'] = response.css('.property-info-feature:not(.beds) span::text').get('').replace('-', '')
        item['MLS'] = response.css('.mls-number ::text').get('').split(':')[-1]

        item['Annual_Tax'] = response.css(
                    'span.amenities-detail-sentence:contains("Tax Annual Amount") + .value::text').get('')
        item['Status'] = "In Market" if response.css('.table-body-row:contains("For Sale")').get() else "Out of Market"
        item['Sold_Date'] = response.css('tr.table-body-row .long-date::text').get()
        item['Lot_Size_Acres'] = response.css('.lotsize span::text').get('')
        if not item['Lot_Size_Acres']:
            response.css('span.amenities-detail-sentence:contains("Acres") + .value::text').get('')
        item['Agent_Email'] = response.css('.agent-information-email::text').get('')

        yield item

    def all_homes_url(self, response):
        return response.css('.for-sale-content-container a::attr(href)').getall()

    def nxt_page(self, response):
        return response.css('.next.text-only').get('')

    def nxt_page_url(self, response):
        return response.urljoin(response.css('#paging ol li:nth-child(3) a::attr(href)')
                                .get('')) + '?' + self.location_property_type

