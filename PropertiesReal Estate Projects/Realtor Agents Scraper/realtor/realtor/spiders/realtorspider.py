import glob
import json
from math import ceil
from datetime import datetime
from urllib.parse import urljoin
from collections import OrderedDict

from scrapy import Spider, Request, Selector


class RealtorspiderSpider(Spider):
    name = "realtorspider"
    allowed_domains = ["www.realtor.com"]
    start_urls = ["https://www.realtor.com"]

    custom_settings = {
        'CONCURRENT_REQUESTS': 4,
        'FEEDS': {
            f'output/{name} Agents Detail {datetime.now().strftime("%d%m%Y%H%M")}.csv': {
                'format': 'csv',
                'fields': ['Name', 'Office', 'Description', 'Experience', 'Areas Served',
                           'Specializations', 'Phone Numbers', 'Website', 'Social Accounts', 'Address', 'For Sale',
                           'Sold', 'Activity Range', 'House Listed', 'URL'],
            }
        }
    }

    headers = {
        'authority': 'www.realtor.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        # 'cookie': '__fp=kZfr3T0xau2iVy7VFxGt; __vst=1a52bf12-37bc-402a-b45d-14e98691506e; split=n; split_tcv=167; __bot=false; s_ecid=MCMID%7C06020846649701655252980916443376396408; _fbp=fb.1.1695199470009.1789912500; _rdt_uuid=1695199470362.51cb7ce5-a4ca-446d-b000-f90d1395d4b1; _gid=GA1.2.742304698.1695199471; _gcl_au=1.1.10710429.1695199472; ajs_anonymous_id=3af6c0e1-3605-4fde-b510-df404ce53260; _scid=86beb143-bcbd-4916-8fa4-c89ae7022e20; ln_or=eyI0ODcyNDIwIjoiZCJ9; _pxvid=f9c63ea2-5791-11ee-972b-dd967fd02010; _tt_enable_cookie=1; _ttp=dvmy6liUl27a13ag58k9zWtNtUv; _tac=false~self|not-available; _ta=us~1~89df68bc35032d48c293adce8574aa42; _sctr=1%7C1695193200000; _iidt=9GStprHlt/PwaqQcoKYGFNJbFF7ibG+UdnCKMIlfI59RxV+yMfQc5liq9kpePF5Rj2cCx28h1JU/aw==; _vid_t=YOKNu1+YXBZ37CYCMkCE9Y/1IXC3pvpCvqpFo0CoVPKHOrvelbpSUQRtSa5vrrtarNGgLmJOE02u4w==; _pin_unauth=dWlkPVl6UXlPVGxpTmpFdFlUbGxOaTAwTnpoaExXRm1NamN0WlRVMVl6RXpabVprWWpNdw; permutive-id=aad03385-41db-41c7-a429-d1cb8bce662b; __ssn=56d994ff-cd0e-41d5-885d-59f228b6d361; __ssnstarttime=1695205496; AMCVS_8853394255142B6A0A4C98A4%40AdobeOrg=1; AMCV_8853394255142B6A0A4C98A4%40AdobeOrg=-1124106680%7CMCIDTS%7C19621%7CMCMID%7C06020846649701655252980916443376396408%7CMCAAMLH-1695810300%7C3%7CMCAAMB-1695810300%7C6G1ynYcLPuiQxYZrsz_pkqfLG9yMXBpb2zX5dvJdYQJzPXImdj0y%7CMCOPTOUT-1695212700s%7CNONE%7CMCAID%7CNONE%7CvVersion%7C5.2.0; pxcts=f45457ec-579f-11ee-b3ca-6cd7202e6a34; AMCVS_AMCV_8853394255142B6A0A4C98A4%40AdobeOrg=1; _tas=7ygbxpn65h8; AMCV_AMCV_8853394255142B6A0A4C98A4%40AdobeOrg=-1124106680%7CMCMID%7C06020846649701655252980916443376396408%7CMCIDTS%7C19621%7CMCOPTOUT-1695215251s%7CNONE%7CvVersion%7C5.2.0; AWSALBTG=RuuUc4Pn3ivaSTTpCQXuTjuN+l7UTl94lQRtJTpmOYI48VvujoNS75iWzUY5EXaDMHkyqS8eBXC/cKPg/uXqxIablfCLQ7r8ej3LIcnH8VJmC8FQo+tjfFQZ5fkl8PnGh+P4LZ4hivw0a8iQ9GzW/QTToI4QaaDHo69wcahIAM6+; AWSALBTGCORS=RuuUc4Pn3ivaSTTpCQXuTjuN+l7UTl94lQRtJTpmOYI48VvujoNS75iWzUY5EXaDMHkyqS8eBXC/cKPg/uXqxIablfCLQ7r8ej3LIcnH8VJmC8FQo+tjfFQZ5fkl8PnGh+P4LZ4hivw0a8iQ9GzW/QTToI4QaaDHo69wcahIAM6+; AWSALB=r/HjjkR+bOxxbX0CfVnUEwWnMO/JTkqn8STlG1NPyzDZ4nNuT0zt2nVEkv9RcxwvSdsu8OSBCDc+Po4EAciGd+pNwPVwZQ8r1L/+jF6T6/VtkgBFIOZDn78iqMVh; AWSALBCORS=r/HjjkR+bOxxbX0CfVnUEwWnMO/JTkqn8STlG1NPyzDZ4nNuT0zt2nVEkv9RcxwvSdsu8OSBCDc+Po4EAciGd+pNwPVwZQ8r1L/+jF6T6/VtkgBFIOZDn78iqMVh; _scid_r=86beb143-bcbd-4916-8fa4-c89ae7022e20; adcloud={%22_les_v%22:%22y%2Crealtor.com%2C1695210637%22}; _ga=GA1.2.1980968069.1695199471; _uetsid=f810b4f0579111ee89b17ba55980bffc; _uetvid=f8113c10579111ee996f39efa020a692; _px3=3fbeb18a81ebf00f7cac3db811233f3099a07d7af8f77285df6648ad6ddc3866:WperEiDSNw3VkbAxoD/e2yYmKFWh2hrnYc+SiQ4lBn31nRugdpc9Dm6JAkkQCOHZMLvN5X3ftLGqJ3LDrlRBPA==:1000:0yaTgCEqVJfcE04bC38pRvile444GCUgq/gXNiIOIt3ZMaUi3ImYG1TS/xZzD41x0n18jAz7qWJ6WcEvTQokTkdA9FFC0mJLkmmVDQJRLc8pQYJZDqQKvqXb2lvHCyu0pV3YtNellNPImcXozZhiJZjUHyyOceuC64LI9dleoQJ5n8EoXXD0SmrJ5qmrIwF4bWYFu4QKQvgeHeUdux5sBHbWL0BW50ROlyiqD0RyO8U=; _ga_MS5EHT6J6V=GS1.1.1695205502.3.1.1695208943.0.0.0',
        # 'referer': 'https://www.realtor.com/realestateagents/85001/pg-3',
        'sec-ch-ua': '"Google Chrome";v="117", "Not;A=Brand";v="8", "Chromium";v="117"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
    }

    def __init__(self):
        self.zipcodes = self.read_zipcode_file()

    def start_requests(self):
        if not self.zipcodes:
            return

        for zipcode in self.zipcodes:
            url = f'https://www.realtor.com/realestateagents/{zipcode}'
            yield Request(url=url, headers=self.headers, callback=self.pagination)

    def pagination(self, response):
        try:
            data = json.loads(response.css('#__NEXT_DATA__ ::text').re_first(r'.*')).get('props', {}).get('pageProps', {})
        except:
            data={}

        total_agents = int(data.get('pageData', {}).get('matching_rows', 0))
        zipcode = data.get('query', {}).get('postalCode', '')
        total_pages = ceil(total_agents / 20)

        for page in range(1, total_pages + 1):
            url = f'https://www.realtor.com/realestateagents/{zipcode}/pg-{page}'
            yield Request(url=url,
                          headers=self.headers,
                          callback=self.parse)

    def parse(self, response, **kwargs):
        agents = response.css('.cardWrapper div.jsx-466393676')
        for agent in agents:
            for_sale = agent.css('.agent-detail-item:contains("For sale") span::text').get('')
            sold = agent.css('.agent-detail-item:contains("Sold") span::text').get('')
            activity_range = agent.css('.agent-detail-item:contains("Activity range") span::text').get('')
            house_listed = agent.css('.agent-detail-item:contains("Listed a house") span::text').get('')
            url = agent.css('.profile-pic a::attr(href)').get('')
            experience = ''.join([x.strip() for x in agent.css('.jIjHAE:contains("Experience") span ::text').getall() if
                                  x.strip()]) or ''
            content = {
                'for_sale': for_sale,
                'sold': sold,
                'activity_range': activity_range,
                'house_listed': house_listed,
                'experience': experience
            }
            yield Request(url=urljoin(response.url, url), headers=self.headers, callback=self.parse_agent,
                          meta={'content': content})

    def parse_agent(self, response):
        try:
            data = json.loads(response.css('#__NEXT_DATA__ ::text').get()).get('props', {}).get('pageProps', {}).get('agentDetails', {})
        except:
            data = {}

        item = OrderedDict()
        item['Name'] = data.get('full_name', '')
        item['Office'] = data.get('broker', {}).get('name', '')
        item['Description'] = data.get('description', '')
        item['Experience'] = response.meta.get('content', {}).get('experience', '')
        item['Areas Served'] = [x.get('name', '') for x in data.get('marketing_area_cities', [])]
        item['Specializations'] = [x.get('name', '') for x in data.get('specializations', [])]
        item['Phone Numbers'] = [x.get('number', '') for x in data.get('phones', [])]
        item['Website'] = data.get('href', '')
        item['Social Accounts'] = [value['href'] for value in data.get('social_media', {}).values()]
        office_name = data.get('office', {}).get('name', '')
        office_address = ', '.join([x.strip() for x in data.get('office', {}).get('address', {}).values() if x.strip()])
        item['Address'] = f'{office_name}, {office_address}'
        item['For Sale'] = response.meta.get('content', {}).get('for_sale', '')
        item['Sold'] = response.meta.get('content', {}).get('sold', '')
        item['Activity Range'] = response.meta.get('content', {}).get('activity_range', '')
        item['House Listed'] = response.meta.get('content', {}).get('house_listed', '')
        item['URL'] = response.url

        yield item

    def read_zipcode_file(self):
        file_name = ''.join(glob.glob('input/zip_codes.txt'))
        try:
            with open(file_name, 'r') as file:
                lines = file.readlines()

            # Strip newline characters and whitespace from each line
            lines = [line.strip() for line in lines]
            return lines
        except:
            return []
