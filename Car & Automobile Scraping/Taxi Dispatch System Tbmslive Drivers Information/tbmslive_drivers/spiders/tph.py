import re
from copy import deepcopy

from scrapy import Spider, Request, FormRequest


class TPHSpider(Spider):
    name = 'tph'
    base_url = 'https://tph.tfl.gov.uk/'
    start_urls = [base_url]

    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 0.5,
    }

    headers = {
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

    def start_requests(self):
        driver_license_page = 'https://tph.tfl.gov.uk/TfL/SearchDriverLicence.page?org.apache.shale.dialog.DIALOG_NAME=TPHDriverLicence&Param=lg2.TPHDriverLicence&menuId=6'

        yield Request(url=driver_license_page, headers=self.headers)

    def parse(self, response, **kwargs):
        license_number = '21082'
        session_id = ''.join(re.findall(r'JSESSIONID=([A-Z\d]+);', response.headers['Set-Cookie'].decode())[:1])

        headers = deepcopy(self.headers)
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

        yield FormRequest(
            url='https://tph.tfl.gov.uk/TfL/lg2/TPHLicensing/pubregsearch/Driver/SearchDriverLicence.page',
            callback=self.search_license,
            method='POST',
            formdata=form_data,
            headers=headers,
            )

    def search_license(self, response):
        license_info = response.css('[title="List of Driver Licences"] tbody tr td ::text').getall()
        license_number = ''.join(license_info[:1])
        holder_name = ''.join(license_info[1:2])
        expiry_date = ''.join(license_info[2:3])
