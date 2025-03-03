from ..items import HomesPropertiesItem

from .basespider import BaseSpider


class HomesSoldSpider(BaseSpider):
    name = "homes_sold"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.prop_type = 5
        self.location_property_type = 'property_type=1,2,260,64'
        self.homes_url = self.all_homes_url
        self.next_page = self.nxt_page
        self.next_page_url = self.nxt_page_url

    def home_detail(self, response):

        dictitems = self.same_selectors(response)
        item = HomesPropertiesItem()
        item.update(dictitems)

        item['Baths'] = response.css('.property-info-feature:not(.beds) span::text').get('')
        item['MLS'] = response.css('.mls-number ::text').get('').split(':')[-1]
        item['Price'] = float(response.css('#price::text').get('').replace('$', '').replace(',', ''))
        item['Property_Tax'] = response.css('.amenities-detail-sentence:contains("Taxable Value") + .value::text').get('')
        if not item['Property_Tax']:
            response.css('.amenities-detail-sentence:contains("Tax") + .value::text').get('')
        item['Zestimate'] = ''
        item['Rent_Zestimate'] = ''
        item['Zestimate_Percentage'] = ''
        item['Latitude'] = ''
        item['Longitude'] = response.css('.amenities-detail-sentence:contains("Longitude:") + .value::text').get('')
        item['Agent_Email'] = response.css('.agent-information-phone-number + span::text').get('')
        item['Status'] = "In Market" if response.css('.table-body-row:contains("For Sale")').get() else "Out of Market"
        item['Sold_Date'] = response.css('tr.table-body-row .long-date::text').get()

        yield item

    def all_homes_url(self, response):
        return response.css('.sold-content-container a::attr(href)').getall()

    def nxt_page(self, response):
        return response.css('.next.text-only').get('')

    def nxt_page_url(self, response):
        return response.urljoin(response.css('#paging ol li:nth-child(3) a::attr(href)')
                                .get('')) + '?' + self.location_property_type
