from ..items import HomesPropertiesItem

from .basespider import BaseSpider


class HomesRentSpider(BaseSpider):
    name = "homes_rent"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.prop_type = 2
        self.location_property_type = 'property_type=1,2,4'
        self.homes_url = self.all_homes_url
        self.next_page = self.nxt_page
        self.next_page_url = self.nxt_page_url

    def home_detail(self, response):
        dictitems = self.same_selectors(response)
        item = HomesPropertiesItem()

        # # Exclude these keys from being added to the item
        excluded_keys = ['Agent_Phone', 'Listing_Office', 'Sqft', 'Listing_Agent']
        dictitems.get('Agent_Phone', '')
        for key, value in dictitems.items():
            if key not in excluded_keys:
                item[key] = value

        item['Broker_Phone'] = dictitems.get('Agent_Phone', '')
        item['Broker_Company'] = dictitems.get('Listing_Office', '')
        item['Broker'] = dictitems.get('Listing_Agent', '')
        item['Area'] = dictitems.get('Sqft', '')

        item['Baths'] = response.css('.property-info-features :nth-child(3) .property-info-feature-detail::text').get('')
        if not item['Baths']:
            response.css('.amenities-detail-sentence:contains("Bathroom") + .value::text').get('')

        item['Price'] = response.css('.rent span::text').get('').replace('$', '').replace(',', '')
        item['Availability_Date'] = ''
        item['Broker_Email'] = response.css('.agent-information-email::text').get('')
        item['Latitude'] = ''
        item['Longitude'] = response.css('.amenities-detail-sentence:contains("Longitude:") + .value::text').get('')

        yield item

    def all_homes_url(self, response):
        return response.css('.for-rent-content-container a::attr(href)').getall()

    def nxt_page(self, response):
        return response.css('.next.text-only').get('')

    def nxt_page_url(self, response):
        return response.urljoin(response.css('#paging ol li:nth-child(3) a::attr(href)')
                                .get('')) + '?' + self.location_property_type


