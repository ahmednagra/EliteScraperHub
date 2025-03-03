import json
import re
from urllib.parse import urljoin
from collections import OrderedDict
from scrapy import Spider, Request


class TripSpider(Spider):
    name = "trip"
    start_urls = ["https://www.tripadvisor.es/FindRestaurants?geo=187529&establishmentTypes=10591&broadened=false"]

    custom_settings = {
        # 'AUTOTHROTTLE_ENABLED': True,
        # 'AUTOTHROTTLE_START_DELAY': 1.0,  # Initial delay in seconds
        # 'AUTOTHROTTLE_TARGET_CONCURRENCY': 0.5,  # Adjust as needed
        # 'AUTOTHROTTLE_DEBUG': True,  # Set to True for debugging

        'CONCURRENT_REQUESTS': 3,
        'FEED_EXPORTERS': {'xlsx': 'scrapy_xlsx.XlsxItemExporter'},
        'FEEDS': {
            f'output/Tripadvisor Articles Details.xlsx': {
                'format': 'xlsx',
                'fields': ['Title', 'Opinions', 'Restaurant Index', 'Address', 'Address 2', 'Phone No', 'Website',
                           'Schedule', 'URL'],
                'overwrite': True
            }
        },
    }

    headers = {
        'authority': 'www.tripadvisor.es',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'max-age=0',
        # 'cookie': 'TAUnique=%1%enc%3AjpgmM5F2Ie4IenR%2FHHpddFs0xDSIJR%2BDyroHIjHxJYBYGBT4tyEnbLAZm7QfivT%2BNox8JbUSTxk%3D; TASameSite=1; TASSK=enc%3AAH79N5fgwCr%2FgDIuh3LXUaIIrmr%2FfbOvCEgqc5JnO5gGZafXdJay3H8K1EqbjrXtlfMCAX38W56qPLCTpN5L35JM9QJtZyO1t7aJ3H4XMpNlWHvx0AcMDFl07upYTP6b9w%3D%3D; pbjs_sharedId=1d665b7f-4506-414a-9327-8f10f0798712; pbjs_sharedId_cst=zix7LPQsHA%3D%3D; _lc2_fpi=684343b8f00b--01hgxbnxghcgtnscbahwmchqp7; _lc2_fpi_meta=%7B%22w%22%3A1701792380433%7D; _ga=GA1.1.1685225728.1701792381; _lr_env_src_ats=false; pbjs_unifiedID=%7B%22TDID%22%3A%2219c2abc1-e06a-4ef3-a2a0-9037234f9f00%22%2C%22TDID_LOOKUP%22%3A%22TRUE%22%2C%22TDID_CREATED_AT%22%3A%222023-11-05T16%3A06%3A26%22%7D; pbjs_unifiedID_cst=zix7LPQsHA%3D%3D; TATrkConsent=eyJvdXQiOiJTT0NJQUxfTUVESUEiLCJpbiI6IkFEVixBTkEsRlVOQ1RJT05BTCJ9; TASID=47A5F9226D7EE63F4A7197D8BF42D535; TADCID=bxuuiEMsvOPBXEFUABQCCKy0j55CTpGVsECjuwJMq3pdBdMgwbajhVKU3BsTI9wzGPYxnf3YCkNKvkVzvrzbzl-0T159DexCQiU; PAC=AFixFFuBo3i5UKlpVBc0WaNx3JMyy1FAKGfh8MZq6oaYKobPiXln1eu6WEGKotAkAYwqKvF9kq_T6buVqMTnl8ybHsXlTnq94OkjtFQR3I3DDHCvbPRoK3MZaapOJcK8Rs4VopcHCECvuYetpVpGvbd5RPu8uuh9itAJJ5QtBciiB8W_Hi4GOH7P_OupyMTRE5fbpxztsWKDJ2EKCRNfE-k%3D; TART=%1%enc%3ArWCXLiBCiwMll9FQODZuLjnoiMmlJrtNrov7tWDfaY9di37qgyhp%2BwDVHbRu918rfYtftmnsPgU%3D; OptanonConsent=isGpcEnabled=0&datestamp=Thu+Dec+21+2023+18%3A44%3A41+GMT%2B0500+(Pakistan+Standard+Time)&version=202310.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=83608b20-4db1-4474-9375-6ead91087deb&interactionCount=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1&AwaitingReconsent=false; _li_dcdm_c=.tripadvisor.es; _ga_QX0Q50ZC9P=GS1.1.1703166282.8.0.1703166282.60.0.0; __gads=ID=06c9609c081e84a1:T=1701792380:RT=1703166283:S=ALNI_MZW1t6EtSNUuC4HRc6YXsUEeLDM2Q; __gpi=UID=00000ce33648b371:T=1701792380:RT=1703166283:S=ALNI_MaujqKjXBoSoOLQJFS8bBmjM7dMMg; _lr_sampling_rate=100; _lr_retry_request=true; __li_idex_cache2_InByZWJpZC82NDQzOT9kdWlkPTY4NDM0M2I4ZjAwYi0tMDFoZ3hibnhnaGNndG5zY2JhaHdtY2hxcDcmcmVzb2x2ZT1ub25JZCZyZXNvbHZlPW1hZ25pdGUi=%7B%7D; __li_idex_cache2_InByZWJpZC82NDQzOT9kdWlkPTY4NDM0M2I4ZjAwYi0tMDFoZ3hibnhnaGNndG5zY2JhaHdtY2hxcDcmcmVzb2x2ZT1ub25JZCZyZXNvbHZlPW1hZ25pdGUi_meta=%7B%22w%22%3A1703166290031%2C%22e%22%3A1703169889000%7D; pbjs_li_nonid=%7B%7D; pbjs_li_nonid_cst=zix7LPQsHA%3D%3D; ab.storage.deviceId.6e55efa5-e689-47c3-a55b-e6d7515a6c5d=%7B%22g%22%3A%22311f4fcf-3829-bf17-0993-d40107c7d46c%22%2C%22c%22%3A1701792378220%2C%22l%22%3A1703166290588%7D; ab.storage.sessionId.6e55efa5-e689-47c3-a55b-e6d7515a6c5d=%7B%22g%22%3A%22cbd637ad-316e-6e63-2242-ebb102b2da23%22%2C%22e%22%3A1703166350614%2C%22c%22%3A1703166290585%2C%22l%22%3A1703166290614%7D; SRT=TART_SYNC; ServerPool=B; PMC=V2*MS.45*MD.20231205*LD.20231221; TATravelInfo=V2*A.2*MG.-1*HP.2*FL.3*RS.1; datadome=ioxGaYvj6DOgoOmx9NC4jAO3Nj6MStjfRoHxVjjmGF~QucuvZ9gHksmj31Z~6~6BdK33~akd_VT~rDTOQKSLoq2_Sv~NbuTSXgKWPai~yDdKz846VNVOojVltXY15XTf; __vt=WbS_uDJDG4eLM4X6ABQCCQPEFUluRFmojcP0P3EgGio6uOmjZ94_Aa-zDSwoyx_rG8LxOZeWdHPLo17I9m8VbKQq1jn74R4ooZ4b1pTf_hCG_0jhxuUWqEHTbQtylWdTSW0rAjD2B4ewn-WMsVRBr1dyOw; TASession=V2ID.47A5F9226D7EE63F4A7197D8BF42D535*SQ.4*LS.FindRestaurants*HS.recommended*ES.popularity*DS.5*SAS.popularity*FPS.oldFirst*FA.1*DF.0*TRA.true*LD.187529*EAU._; TAUD=LA-1703166719945-1*RDD-1-2023_12_21*LG-685919-2.1.F.*LD-685920-.....',
        'sec-ch-device-memory': '8',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-arch': '"x86"',
        'sec-ch-ua-full-version-list': '"Not_A Brand";v="8.0.0.0", "Chromium";v="120.0.6099.110", "Google Chrome";v="120.0.6099.110"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-model': '""',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }

    cookies = {
        'TAUnique': '%1%enc%3AjpgmM5F2Ie4IenR%2FHHpddFs0xDSIJR%2BDyroHIjHxJYBYGBT4tyEnbLAZm7QfivT%2BNox8JbUSTxk%3D',
        'TASameSite': '1',
        'TASSK': 'enc%3AAH79N5fgwCr%2FgDIuh3LXUaIIrmr%2FfbOvCEgqc5JnO5gGZafXdJay3H8K1EqbjrXtlfMCAX38W56qPLCTpN5L35JM9QJtZyO1t7aJ3H4XMpNlWHvx0AcMDFl07upYTP6b9w%3D%3D',
        'pbjs_sharedId': '1d665b7f-4506-414a-9327-8f10f0798712',
        'pbjs_sharedId_cst': 'zix7LPQsHA%3D%3D',
        '_lc2_fpi': '684343b8f00b--01hgxbnxghcgtnscbahwmchqp7',
        '_lc2_fpi_meta': '%7B%22w%22%3A1701792380433%7D',
        '_ga': 'GA1.1.1685225728.1701792381',
        '_lr_env_src_ats': 'false',
        'pbjs_unifiedID': '%7B%22TDID%22%3A%2219c2abc1-e06a-4ef3-a2a0-9037234f9f00%22%2C%22TDID_LOOKUP%22%3A%22TRUE%22%2C%22TDID_CREATED_AT%22%3A%222023-11-05T16%3A06%3A26%22%7D',
        'pbjs_unifiedID_cst': 'zix7LPQsHA%3D%3D',
        'TATrkConsent': 'eyJvdXQiOiJTT0NJQUxfTUVESUEiLCJpbiI6IkFEVixBTkEsRlVOQ1RJT05BTCJ9',
        'TASID': '47A5F9226D7EE63F4A7197D8BF42D535',
        'TADCID': 'bxuuiEMsvOPBXEFUABQCCKy0j55CTpGVsECjuwJMq3pdBdMgwbajhVKU3BsTI9wzGPYxnf3YCkNKvkVzvrzbzl-0T159DexCQiU',
        'PAC': 'AFixFFuBo3i5UKlpVBc0WaNx3JMyy1FAKGfh8MZq6oaYKobPiXln1eu6WEGKotAkAYwqKvF9kq_T6buVqMTnl8ybHsXlTnq94OkjtFQR3I3DDHCvbPRoK3MZaapOJcK8Rs4VopcHCECvuYetpVpGvbd5RPu8uuh9itAJJ5QtBciiB8W_Hi4GOH7P_OupyMTRE5fbpxztsWKDJ2EKCRNfE-k%3D',
        'TART': '%1%enc%3ArWCXLiBCiwMll9FQODZuLjnoiMmlJrtNrov7tWDfaY9di37qgyhp%2BwDVHbRu918rfYtftmnsPgU%3D',
        'OptanonConsent': 'isGpcEnabled=0&datestamp=Thu+Dec+21+2023+18%3A44%3A41+GMT%2B0500+(Pakistan+Standard+Time)&version=202310.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=83608b20-4db1-4474-9375-6ead91087deb&interactionCount=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0003%3A1%2CC0004%3A1&AwaitingReconsent=false',
        '_li_dcdm_c': '.tripadvisor.es',
        '_ga_QX0Q50ZC9P': 'GS1.1.1703166282.8.0.1703166282.60.0.0',
        '__gads': 'ID=06c9609c081e84a1:T=1701792380:RT=1703166283:S=ALNI_MZW1t6EtSNUuC4HRc6YXsUEeLDM2Q',
        '__gpi': 'UID=00000ce33648b371:T=1701792380:RT=1703166283:S=ALNI_MaujqKjXBoSoOLQJFS8bBmjM7dMMg',
        '_lr_sampling_rate': '100',
        '_lr_retry_request': 'true',
        '__li_idex_cache2_InByZWJpZC82NDQzOT9kdWlkPTY4NDM0M2I4ZjAwYi0tMDFoZ3hibnhnaGNndG5zY2JhaHdtY2hxcDcmcmVzb2x2ZT1ub25JZCZyZXNvbHZlPW1hZ25pdGUi': '%7B%7D',
        '__li_idex_cache2_InByZWJpZC82NDQzOT9kdWlkPTY4NDM0M2I4ZjAwYi0tMDFoZ3hibnhnaGNndG5zY2JhaHdtY2hxcDcmcmVzb2x2ZT1ub25JZCZyZXNvbHZlPW1hZ25pdGUi_meta': '%7B%22w%22%3A1703166290031%2C%22e%22%3A1703169889000%7D',
        'pbjs_li_nonid': '%7B%7D',
        'pbjs_li_nonid_cst': 'zix7LPQsHA%3D%3D',
        'ab.storage.deviceId.6e55efa5-e689-47c3-a55b-e6d7515a6c5d': '%7B%22g%22%3A%22311f4fcf-3829-bf17-0993-d40107c7d46c%22%2C%22c%22%3A1701792378220%2C%22l%22%3A1703166290588%7D',
        'ab.storage.sessionId.6e55efa5-e689-47c3-a55b-e6d7515a6c5d': '%7B%22g%22%3A%22cbd637ad-316e-6e63-2242-ebb102b2da23%22%2C%22e%22%3A1703166350614%2C%22c%22%3A1703166290585%2C%22l%22%3A1703166290614%7D',
        'SRT': 'TART_SYNC',
        'ServerPool': 'B',
        'PMC': 'V2*MS.45*MD.20231205*LD.20231221',
        'TATravelInfo': 'V2*A.2*MG.-1*HP.2*FL.3*RS.1',
        'datadome': 'ioxGaYvj6DOgoOmx9NC4jAO3Nj6MStjfRoHxVjjmGF~QucuvZ9gHksmj31Z~6~6BdK33~akd_VT~rDTOQKSLoq2_Sv~NbuTSXgKWPai~yDdKz846VNVOojVltXY15XTf',
        '__vt': 'WbS_uDJDG4eLM4X6ABQCCQPEFUluRFmojcP0P3EgGio6uOmjZ94_Aa-zDSwoyx_rG8LxOZeWdHPLo17I9m8VbKQq1jn74R4ooZ4b1pTf_hCG_0jhxuUWqEHTbQtylWdTSW0rAjD2B4ewn-WMsVRBr1dyOw',
        'TASession': 'V2ID.47A5F9226D7EE63F4A7197D8BF42D535*SQ.4*LS.FindRestaurants*HS.recommended*ES.popularity*DS.5*SAS.popularity*FPS.oldFirst*FA.1*DF.0*TRA.true*LD.187529*EAU._',
        'TAUD': 'LA-1703166719945-1*RDD-1-2023_12_21*LG-685919-2.1.F.*LD-685920-.....',
    }

    def start_requests(self):
        yield Request(url=self.start_urls[0], callback=self.parse, headers=self.headers, cookies=self.cookies)

    def parse(self, response, **kwargs):
        resturants = response.css(
            '.iyHmZ.b.o.W.q::attr(href) , .Ikpld.f.e .BMQDV._F.Gv.wSSLS.SwZTJ.FGwzt.ukgoS::attr(href)').getall()
        for resturant in resturants:
            yield Request(url=urljoin(self.start_urls[0], resturant), callback=self.parse_hotel, headers=self.headers)

        next_page = response.css('[data-smoke-attr="pagination-next-arrow"]::attr(href)').get('')
        if next_page:
            yield Request(url=urljoin(self.start_urls[0], next_page), callback=self.parse, headers=self.headers)

    def parse_hotel(self, response):
        data = response.css('script:contains(__WEB_CONTEXT__)').re_first(r'({.*?});\(this\.\$WP=')
        if data:
            schedule = re.findall(r'"display_hours":\s*\[({.*?})]', data)
            schedule = json.loads(f'[{",".join(schedule)}]')
            final_schedule = self.get_schedule(schedule)
            website = ''.join(re.findall(r'"website":"(https?://[^"]+)"', data))
        else:
            final_schedule = ''
            website = ''

        selector = response.css('[data-test-target="restaurant-detail-info"]')
        item = OrderedDict()

        item['Title'] = selector.css('h1::text').get('')
        item['Opinions'] = selector.css('.AfQtZ::text').get('')
        item['Restaurant Index'] = selector.css('.DsyBj.cNFrA a span span::text').get('').replace('#', '')

        address = selector.css('.dlMOJ ::text').getall()
        item['Address'] = ', '.join(address) if address else ''

        address_2 = selector.css('.AYHFM ::text').getall()
        if len(address_2) >= 3:
            item['Address 2'] = address_2[2]
        else:
            item['Address 2'] = ''

        item['Phone No'] = selector.css('.DsyBj.cNFrA .BMQDV._F.Gv.wSSLS.SwZTJ::text').get('')
        item['Website'] = website
        item['Schedule'] = final_schedule
        item['URL'] = response.url

        yield item

    def get_schedule(self, schedule):
        # Define a mapping for days of the week
        days_mapping = {
            'lun': 'lun',
            'mar': 'mar',
            'mié': 'mié',
            'jue': 'jue',
            'vie': 'vie',
            'sáb': 'sáb',
            'dom': 'dom',
        }

        formatted_schedule = []

        # Iterate through each schedule entry
        for entry in schedule:
            days_range = entry['days']
            times_range = entry['times'][0]  # Assuming there is only one time range in the list

            # Split the days range into individual days
            start_time, end_time = [time.strip() for time in times_range.split('-')]

            # Determine whether to use 'de la mañana' or 'de la tarde'
            start_hour = int(start_time.split(':')[0])
            start_period = 'de la tarde' if 12 <= start_hour < 24 else 'de la mañana'

            end_hour = int(end_time.split(':')[0])
            end_period = 'de la tarde' if 12 <= end_hour < 24 else 'de la mañana'

            # # Convert 24-hour format to 12-hour format
            start_time_12h = self.convert_to_12_hour_format(start_time)
            end_time_12h = self.convert_to_12_hour_format(end_time)

            # Format the output for each day in the range
            days_list = [day.strip() for day in days_range.split('-')]
            for day in days_list:
                formatted_day = f'{days_mapping[day]}  {start_time_12h} {start_period} - {end_time_12h} {end_period}'
                formatted_schedule.append(formatted_day)

        # Join the formatted days into a single string
        result_string = ',\n'.join(formatted_schedule)

        return result_string

    def convert_to_12_hour_format(self, time_24h):
        hour, minute = map(int, time_24h.split(':'))
        hour = hour % 12 or 12  # Ensure 12:00 is displayed as 12:00, not 0:00
        return f'{hour:02d}:{minute:02d}'
