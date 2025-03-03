
import json
import re
from copy import deepcopy

from urllib.parse import urljoin

from scrapy import Spider, Request, FormRequest

from .methods import write_to_excel, upload_file_to_drive


class TbmsliveSpider(Spider):
    name = 'tbmslive_drivers'
    start_urls = ['https://ge.tbmslive.com/']

    drivers_data = []
    form_data = {}

    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 0.5,
    }

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'Connection': 'keep-alive',
        # 'Cookie': 'PHPSESSID=rlq1l7g1dde3qogad00ic21o6l; base_name=ac247; form_name=admin; form_pass=admin',
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
        # 'Cookie': 'JSESSIONID=BE985FFDC6C0024D1B06E094D31B1F85; hide-cookies-panel=yes',
        'Origin': 'https://tph.tfl.gov.uk',
        'Referer': 'https://tph.tfl.gov.uk/TfL/home.page',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.drivers_data = []

    def start_requests(self):
        url = 'https://ge.tbmslive.com/index.php'
        yield Request(url=url, headers=self.headers, callback=self.parse_login_page)

    def parse_login_page(self, response):
        phpsessionid = response.headers['Set-Cookie']
        phpsessionid = phpsessionid.decode('utf-8')
        phpsessionid_parts = phpsessionid.split('; ')
        cookie_dict = {}

        for part in phpsessionid_parts[:1]:
            try:
                key, value = part.split('=')
                cookie_dict[key] = value
            except ValueError:
                continue

        self.form_data = {
            'PHPSESSID': cookie_dict['PHPSESSID'],
            'base_name': 'ac247',
            'form_name': 'admin',
            'form_pass': 'admin',
        }

        url = 'https://ge.tbmslive.com/index.php'

        yield FormRequest(url=url, formdata=self.form_data, headers=self.headers, callback=self.parse_login_result)

    def parse_login_result(self, response):

        yield Request(url='https://ge.tbmslive.com/driver.php', headers=self.headers, cookies=self.form_data,
                      callback=self.home_page)

    def home_page(self, response):
        driver_urls = response.css('.table.table-bordered td:nth-child(3)').re(r"window\.open\('([^']+)'\)")
        driver_urls = [url.replace('amp;', '') for url in driver_urls]

        for driver in driver_urls:
            # url = urljoin(response.url, driver)
            url = 'https://ge.tbmslive.com/tbms_driver.php?action=edit&uid=137'

            yield Request(url=url, headers=self.headers, cookies=self.form_data, callback=self.driver_detail)

    def driver_detail(self, response):

        driver_name = response.css('#user_name::attr(value)').get()
        driver_license = response.css('#driver_pco_licence_number::attr(value)').get('')[:5]
        vehicle_licence_expiry = response.css('#vehicle_pco_licence_expiry::attr(value)').get('')
        vehicle_licence_no = response.css('#vehicle_pco_licence_number::attr(value)').get('')
        driver_licence_expiry = response.css('#driver_pco_licence_expiry::attr(value)').get('')

        # self.drivers_data.append([
        #     driver_name, driver_license, driver_licence_expiry, vehicle_licence_no, vehicle_licence_expiry])

        driver_license_page = 'https://tph.tfl.gov.uk/TfL/SearchDriverLicence.page?org.apache.shale.dialog.DIALOG_NAME=TPHDriverLicence&Param=lg2.TPHDriverLicence&menuId=6'

        yield Request(url=driver_license_page, headers=self.headers_tph,
                      callback=self.tph_website_index,
                      meta={'driver_license': driver_license, 'vehicle_licence_no': vehicle_licence_no}
                      )

    def tph_website_index(self, response):
        a = 1
        try:
            license_number = response.meta['driver_license']
        except (KeyError, TypeError):
            license_number = {}

        try:
            vehicle_licence_no = response.meta['vehicle_licence_no']
        except (KeyError, TypeError):
            vehicle_licence_no = {}

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

        session_id = ''.join(re.findall(r'JSESSIONID=([A-Z\d]+);', response.headers['Set-Cookie'].decode())[:1])

        headers = deepcopy(self.headers)
        headers['Cookie'] = f'JSESSIONID={session_id}; hide-cookies-panel=yes'
        headers['Referer'] = response.url
        # url = 'https://tph.tfl.gov.uk/TfL/lg2/TPHLicensing/pubregsearch/Driver/SearchDriverLicence.page'
        url = 'https://tph.tfl.gov.uk/TfL/SearchDriverLicence.page?org.apache.shale.dialog.DIALOG_NAME=TPHDriverLicence&Param=lg2.TPHDriverLicence&menuId=6'
        yield FormRequest(
            url=url,
            callback=self.search_license,
            method='POST',
            formdata=form_data,
            headers=self.headers_tph,
        )

    def search_license(self, response):
        license_info = response.css('[title="List of Driver Licences"] tbody tr td ::text').getall()
        license_number = ''.join(license_info[:1])
        holder_name = ''.join(license_info[1:2])
        expiry_date = ''.join(license_info[2:3])


    def closed(self, reason):
        sheet_name = 'drivers_report'
        file_name = write_to_excel(self.drivers_data, sheet_name)
        upload_file_to_drive(file_name)

