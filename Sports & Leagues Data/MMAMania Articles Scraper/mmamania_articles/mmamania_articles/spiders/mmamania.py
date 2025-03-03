import csv
import json
import re
from collections import OrderedDict

import requests
from scrapy import Spider, Request

from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import gsheets


class MmaManiaSpider(Spider):
    name = 'mmamania'

    base_url = 'https://www.mmamania.com/'

    headers = {
        'authority': 'www.mmamania.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36',
    }

    custom_settings = {
        'CONCURRENT_REQUESTS': 3,
        'DOWNLOAD_DELAY': 2,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.scope = ["https://spreadsheets.google.com/feeds", 'https://www.googleapis.com/auth/spreadsheets',
                      "https://www.googleapis.com/auth/drive.file", "https://www.googleapis.com/auth/drive"]

        self.creds = ServiceAccountCredentials.from_json_keyfile_name('input/google_credentials.json', self.scope)

        self.gsheet_config = self.get_key_values_from_file('input/googlesheet_keys.txt')
        self.google_sheet_csv_download_url_t = 'https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&id={spreadsheet_id}&gid={tab_id}'

        google_sheet_data = self.get_googlesheet_data()
        self.gsheet_scraped_items_urls = [item.get('Article URL', '') for item in google_sheet_data]

        self.current_scraped_items = []

    def start_requests(self):

        yield Request(url=self.base_url, headers=self.headers)

    def parse(self, response, **kwargs):
        articles = response.css('.c-five-up__col .c-five-up__entry, .c-compact-river .c-compact-river__entry')
        thumbnails_data = self.get_thumbnail_data(articles)

        for row in articles:
            if 'data-native-ad-id' in row.get():
                continue

            url = row.css('a::attr(href)').get('')
            thumbnail_text = row.css('.c-entry-box--compact__title a::text').get('')
            thumbnail_img = self.get_thumbnail_url(row, thumbnails_data)

            if not url:
                continue

            if url in self.gsheet_scraped_items_urls:
                continue

            main_image = row.css('noscript img ::attr(src)').get('')

            yield Request(url=url, headers=self.headers, callback=self.parse_detail,
                          meta={'main_image': main_image, 'thumbnail_text': thumbnail_text,
                                'thumbnail_image': thumbnail_img})

    def parse_detail(self, response):
        article_url = response.url

        if article_url in self.gsheet_scraped_items_urls:
            return

        description = response.xpath("//div[@class='c-entry-content ']//*[not(ancestor::aside)]").getall()
        description = ''.join(description)[:32700]

        item = OrderedDict()
        item['Title'] = response.css('.c-page-title ::text').get('').strip()
        item['Thumbnail Title'] = response.meta.get('thumbnail_text', '')
        category = ', '.join(
            x.strip() for x in response.css('[aria-labelledby="heading-label--ov8rafdn"] ::text').getall() if x.strip())
        category = category or ', '.join(
            x.strip() for x in response.css('.c-entry-group-labels__item ::text').getall() if x.strip())
        item['Category'] = category
        item['Summary'] = response.css('.c-entry-summary ::text').get('')
        item['Thumbnail URL'] = response.meta.get('thumbnail_image', '')
        item['Image URL'] = self.get_image_url(response)
        item['Image Text'] = response.css('.e-image--hero .e-image__meta cite ::text').get('')
        item['Description HTML'] = f'<div>{description}</div>'
        item['Published At'] = response.css('[data-ui="timestamp"] ::text').get('').strip()
        item['Article URL'] = article_url

        self.current_scraped_items.append(item)

        yield item

    def get_googlesheet_data(self):
        filename = 'gsheet_data.csv'

        self.download_google_sheet_data_as_csv(filename)

        with open(filename, mode='r', encoding='utf-8') as data_file:
            data = csv.DictReader(data_file)
            # columns = data.fieldnames
            return [row for row in data]

    def download_google_sheet_data_as_csv(self, filename):
        spreadsheet_id = self.gsheet_config.get('googlesheet_id')

        gsheet_url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}"

        sheets = gsheets.Sheets(self.creds)
        sheet = sheets.get(gsheet_url)
        sheet[0].to_csv(filename)

    def update_google_sheet(self):
        if not self.current_scraped_items:
            self.logger.debug('\n\nThere is no new article found...!!!\n\n')
            return

        columns = [[col for col in row.keys()] for row in self.current_scraped_items][:1]
        rows_values = [[value for value in row.values()] for row in self.current_scraped_items]

        if not self.gsheet_scraped_items_urls:
            rows_values = columns + [[value for value in row.values()] for row in self.current_scraped_items]

        spreadsheet_id = self.gsheet_config.get('googlesheet_id')
        tab_sheet_name = self.gsheet_config.get(f'tab_name')

        service = build('sheets', 'v4', credentials=self.creds)

        # Determine the last row with data
        last_row_range = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=f"{tab_sheet_name}!A:A"
        ).execute()
        last_row_index = len(last_row_range.get('values', [])) + 1

        # Append data starting from the first empty row
        range_to_append = f"{tab_sheet_name}!A{last_row_index}"

        # append data
        service.spreadsheets().values().append(spreadsheetId=spreadsheet_id,
                                               range=range_to_append,
                                               body={
                                                   "majorDimension": "ROWS",
                                                   "values": rows_values  # representing each row values as list. So it contains as list of lists
                                               },
                                               valueInputOption="USER_ENTERED").execute()

        self.logger.debug(f'\n\nNew Articles Found: "{len(self.current_scraped_items)}"')
        self.logger.debug(f'Google Sheet "{tab_sheet_name}" has been updated\n\n')

    def get_key_values_from_file(self, file_path):
        """
        Get the Google sheet keys and Search URLs keys  from input text file
        """

        with open(file_path, mode='r', encoding='utf-8') as input_file:
            data = {}

            for row in input_file.readlines():
                if not row.strip():
                    continue

                try:
                    key, value = row.strip().split('==')
                    data.setdefault(key.strip(), value.strip())
                except ValueError:
                    pass

            return data

    def get_thumbnail_url(self, row, data):
        thumbnail_image = row.css('source::attr(srcset)').get('').split(',')[0].replace('300w', '').replace('600w',
                                                                                                            '').strip()
        thumbnail_image_url = re.search(r'^(.*\.jpg)', thumbnail_image).group(1) if re.search(r'^(.*\.jpg)',
                                                                                              thumbnail_image) else ''
        if not thumbnail_image_url:
            selector = row.css('img::attr(data-cdata)').get('')
            try:
                id = json.loads(selector).get('image_id', 0)
                id = str(id)
            except Exception as e:
                print(e)
                id = {}

            if [x for x in data.keys() if id in x]:
                thumbnail_image_url = ''.join([x for x in data.values() if id in x])
            else:
                try:
                    res = requests.get(
                        url=f'https://www.mmamania.com/services/optimally_sized_images?imgkeys={id}:*:1:205x115:&asset_keys=')
                    res_data = res.json().get('urls', {})
                except Exception as e:
                    res_data = {}

                if [x for x in res_data.keys() if id in x]:
                    thumbnail_image_url = ''.join([x for x in res_data.values() if id in x])
                else:
                    thumbnail_image_url = ''

        return thumbnail_image_url

    def get_thumbnail_data(self, articles):
        ids_selector = articles.css('img::attr(data-cdata)').getall()
        id_list = [int(entry.split('"image_id":')[1].split(",")[0]) for entry in ids_selector]
        resolution = '273x154'
        format = 'webp'
        base_url = 'https://www.mmamania.com/services/optimally_sized_images?imgkeys='
        id_string = ','.join(f'{id}:*:1:{resolution}:{format}' for id in id_list)
        url = f'{base_url}{id_string}&asset_keys='

        try:
            res = requests.get(url=url)
            data = res.json().get('urls', {})
        except Exception as e:
            data = {}

        return data

    def get_image_url(self, response):
        url = ''.join(response.css('.l-article-body-segment source::attr(srcset)').get('').split(',')[3:4])
        if url:
            if 'jpeg' in url:
                url = url.split('jpeg')[0] + 'jpeg'
            elif 'jpg' in url:
                url = url.split('jpg')[0] + 'jpg'
        else:
            url = ''

        return url.strip()

    def close(spider, reason):
        spider.update_google_sheet()
