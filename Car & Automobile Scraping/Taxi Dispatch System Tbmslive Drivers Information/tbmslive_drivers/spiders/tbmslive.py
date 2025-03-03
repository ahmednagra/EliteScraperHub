import re
from copy import deepcopy
from datetime import datetime
from urllib.parse import urljoin

from scrapy import Spider, Request, FormRequest, signals

from .methods import write_to_excel, upload_file_to_drive


class TbmsliveSpider(Spider):
    name = 'tbmslive_drivers'
    base_url = 'https://ge.tbmslive.com/'

    login_page_url = 'https://ge.tbmslive.com/index.php'

    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 0.5,
    }

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    headers_tph = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Origin': 'https://tph.tfl.gov.uk',
        'Referer': 'https://tph.tfl.gov.uk/TfL/home.page',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver_items = dict()
        self.driver_urls = []

        self.tbmslive_auth_session = {}

    def start_requests(self):
        yield Request(url=self.login_page_url, headers=self.headers, callback=self.parse_login_page)

    def parse(self, response, **kwargs):
        pass

    def parse_login_page(self, response):
        phpsessionid = response.headers['Set-Cookie']
        phpsessionid = phpsessionid.decode('utf-8')
        phpsessionid_parts = phpsessionid.split('; ')
        cookie_dict = {}

        login_credentials = self.get_login_creds_from_file()

        for part in phpsessionid_parts[:1]:
            try:
                key, value = part.split('=')
                cookie_dict[key] = value
            except ValueError:
                continue

        self.tbmslive_auth_session = {
            'PHPSESSID': cookie_dict['PHPSESSID'],
            'base_name': login_credentials.get('office_name'),
            'form_name': login_credentials.get('operator_name'),
            'form_pass': login_credentials.get('operator_password'),
        }

        yield FormRequest(url=self.login_page_url,
                          formdata=self.tbmslive_auth_session,
                          headers=self.headers,
                          callback=self.parse_login_result
                          )

    def parse_login_result(self, response):

        yield Request(url='https://ge.tbmslive.com/driver.php', headers=self.headers, cookies=self.tbmslive_auth_session,
                      callback=self.home_page)

    def home_page(self, response):
        driver_urls = response.css('.table.table-bordered td:nth-child(3)').re(r"window\.open\('([^']+)'\)")
        self.driver_urls = [url.replace('amp;', '') for url in driver_urls][25:35]

        self.logger.info(f'Total No. of Driver: {len(self.driver_urls)}')

    def driver_detail(self, response):

        driver_name = response.css('#user_name::attr(value)').get()
        driver_pco_license = response.css('#driver_pco_licence_number::attr(value)').get('')
        driver_license = response.css('#driver_pco_licence_number::attr(value)').get('')[:5]
        veh_pco_licence = response.css('#vehicle_pco_licence_number::attr(value)').get('')[:6]

        self.driver_items[driver_name] = dict()
        self.driver_items[driver_name]['Name'] = driver_name or ''
        self.driver_items[driver_name]['Driver PCO License'] = driver_pco_license or ''
        self.driver_items[driver_name]['Veh PCO Licence'] = veh_pco_licence or ''

        if not driver_license and not veh_pco_licence:
            return

        driver_license_page = 'https://tph.tfl.gov.uk/TfL/SearchDriverLicence.page?org.apache.shale.dialog.DIALOG_NAME=TPHDriverLicence&Param=lg2.TPHDriverLicence&menuId=6'
        vehicle_license_page = 'https://tph.tfl.gov.uk/TfL/SearchVehicleLicence.page?org.apache.shale.dialog.DIALOG_NAME=TPHVehicleLicence&Param=lg2.TPHVehicleLicence&menuId=7'

        if driver_license:
            yield Request(url=driver_license_page,
                          headers=self.headers_tph,
                          callback=self.tph_driver_index,
                          meta={'driver_license': driver_license, 'name': driver_name, 'dont_merge_cookies': True},
                          dont_filter=True
                          )

        if veh_pco_licence:
            yield Request(url=vehicle_license_page,
                          headers=self.headers_tph,
                          callback=self.tph_vehicle_index,
                          meta={'vehicle_licence_no': veh_pco_licence, 'name': driver_name, 'dont_merge_cookies': True},
                          dont_filter=True,
                          )

    def tph_driver_index(self, response):
        try:
            license_number = response.meta['driver_license']
        except (KeyError, TypeError):
            license_number = {}

        session_id = ''.join(re.findall(r'JSESSIONID=([A-Z\d]+);', response.headers['Set-Cookie'].decode())[:1])

        headers = deepcopy(self.headers_tph)
        headers['Cookie'] = f'JSESSIONID={session_id}; hide-cookies-panel=yes'
        headers['Referer'] = response.url

        form_data = {
            'javax.faces.ViewState': response.css('[name="javax.faces.ViewState"]::attr(value)').get(''),
            'searchdriverlicenceform:DriverLicenceNo': license_number,
            'searchdriverlicenceform:ContactObjSurname': '',
            'searchdriverlicenceform:ContactObjForenames': '',
            'searchdriverlicenceform:_id189': 'Search',
            'searchdriverlicenceform_SUBMIT': '1',
            'Civica.CSRFToken': response.css('input[name="Civica.CSRFToken"]::attr(value)').get(''),
            'searchdriverlicenceform:_idcl': '',
            'searchdriverlicenceform:_link_hidden_': '',
        }

        url = 'https://tph.tfl.gov.uk/TfL/lg2/TPHLicensing/pubregsearch/Driver/SearchDriverLicence.page'

        yield FormRequest(
            url=url,
            callback=self.search_license,
            method='POST',
            formdata=form_data,
            headers=headers,
            meta=response.meta,
        )

    def search_license(self, response):
        name = response.meta['name']

        license_info = response.css('[title="List of Driver Licences"] tbody tr td ::text').getall()
        licence_holder_name = ''.join(license_info[1:2]).strip()
        expiry_date = self.convert_date_to_dmy_format(''.join(license_info[2:3]).strip())

        if name in self.driver_items:
            self.driver_items[name]['Licence Holder Name'] = licence_holder_name or ''
            self.driver_items[name]['Driver PCO Licence Expiry'] = expiry_date or ''

    def tph_vehicle_index(self, response):
        try:
            vehicle_licence_no = response.meta['vehicle_licence_no']
        except (KeyError, TypeError):
            vehicle_licence_no = {}

        session_id = ''.join(re.findall(r'JSESSIONID=([A-Z\d]+);', response.headers['Set-Cookie'].decode())[:1])

        headers = deepcopy(self.headers_tph)
        headers['Cookie'] = f'JSESSIONID={session_id}; hide-cookies-panel=yes'
        headers['Referer'] = response.url

        vehicle_form_data = {
            'javax.faces.ViewState': response.css('[name="javax.faces.ViewState"]::attr(value)').get(''),
            'searchvehiclelicenceform:VehicleVRM': '',
            'searchvehiclelicenceform:VehiclePlateDiscNo': vehicle_licence_no,
            'searchvehiclelicenceform:VehicleMake': '',
            'searchvehiclelicenceform:VehicleModel': '',
            'searchvehiclelicenceform:_id187': 'Search',
            'searchvehiclelicenceform_SUBMIT': '1',
            'Civica.CSRFToken': response.css('input[name="Civica.CSRFToken"]::attr(value)').get(''),
            'searchvehiclelicenceform:_link_hidden_': '',
            'searchvehiclelicenceform:_idcl': '',
        }

        url = 'https://tph.tfl.gov.uk/TfL/lg2/TPHLicensing/pubregsearch/Vehicle/SearchVehicleLicence.page'
        yield FormRequest(
            url=url,
            callback=self.search_vehicle,
            method='POST',
            formdata=vehicle_form_data,
            headers=headers,
            meta=response.meta
        )

    def search_vehicle(self, response):
        driver_name = response.meta['name']

        vehicle_registration_no = self.get_value_of(response, keyword='Registration Number')
        vehicle_make = self.get_value_of(response, keyword='Make')
        vehicle_model = self.get_value_of(response, keyword='Model')
        vehicle_licence_expire = self.convert_date_to_dmy_format(self.get_value_of(response, keyword='Licence Expiry Date'))
        vehicle_plate = self.get_value_of(response, keyword='Plate/ Disc Number')

        if driver_name in self.driver_items:
            self.driver_items[driver_name]['Veh PCO Licence Expiry'] = vehicle_licence_expire or ''
            self.driver_items[driver_name]['Vehicle Plate/ Disc Number'] = vehicle_plate or ''
            self.driver_items[driver_name]['Vehicle Registration Number (VRM)'] = vehicle_registration_no or ''
            self.driver_items[driver_name]['Vehicle Make'] = vehicle_make or ''
            self.driver_items[driver_name]['Vehicle Model'] = vehicle_model or ''

    def get_value_of(self, response, keyword):
        value = response.css(f'p:contains("{keyword}") ::text').re_first(':(.*)')

        return value.strip() if value else ''

    def get_login_creds_from_file(self):
        with open('input/login.txt', mode='r') as login_file:
            login_credentials = {}
            data = [line.strip() for line in login_file.readlines() if line.strip()]

            for line in data:
                key, value = line.split(':')
                login_credentials[key] = value.strip()

        return login_credentials

    def convert_date_to_dmy_format(self, date_str):
        date_formats = ['%Y/%m/%d', '%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']

        for date_format in date_formats:
            try:
                date_obj = datetime.strptime(date_str, date_format)
                date_formatted = date_obj.strftime('%d/%m/%Y')
                return date_formatted
            except ValueError:
                return ''

    def spider_idle(self, spider):
        if self.driver_urls:
            driver_url = self.driver_urls.pop(0)
            self.logger.info(f'Remaining No. of Driver: {len(self.driver_urls)}')

            request = Request(url=urljoin(self.base_url, driver_url), headers=self.headers,
                              cookies=self.tbmslive_auth_session, callback=self.driver_detail)
            self.crawler.engine.crawl(request, spider)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(TbmsliveSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_idle, signal=signals.spider_idle)

        return spider

    def closed(self, reason):
        sheet_name = 'drivers_report'
        data = self.driver_items
        file_name = write_to_excel(data, sheet_name)
        upload_file_to_drive(file_name)
