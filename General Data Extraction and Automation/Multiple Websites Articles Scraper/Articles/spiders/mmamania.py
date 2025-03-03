import csv
from collections import OrderedDict

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
        self.gsheet_scraped_items_urls = [item['Article URL'] for item in google_sheet_data]

        self.current_scraped_items = []

    def start_requests(self):

        yield Request(url=self.base_url, headers=self.headers)

    def parse(self, response, **kwargs):
        # articles = response.css('[data-analytics-link="article:image"]')
        articles = response.css('.c-five-up__col .c-five-up__entry, .c-compact-river .c-compact-river__entry')

        for row in articles:
            url = row.css('a::attr(href)').get('')
            thumbnail_text = row.css('.c-entry-box--compact__title a::text').get('')

            if not url:
                continue

            if url in self.gsheet_scraped_items_urls:
                continue

            main_image = row.css('noscript img ::attr(src)').get('') or row.css('img::attr(src)').get('')

            yield Request(url=url, headers=self.headers, callback=self.parse_detail, meta={'main_image': main_image, 'thumbnail_text': thumbnail_text})

    def parse_detail(self, response):
        article_url = response.url

        if article_url in self.gsheet_scraped_items_urls:
            return

        description = response.xpath("//div[@class='c-entry-content ']//*[not(ancestor::aside)]").getall()
        description = ''.join(description)[:32700]

        main_image_url = ''.join(response.css('.e-image--hero img::attr(src)').get('').split('/cdn.vox-cdn.com')[-1:])

        main_image_url = f'https://cdn.vox-cdn.com{main_image_url}' if main_image_url else response.meta.get('main_image', '')

        item = OrderedDict()
        item['Title'] = response.css('.c-page-title ::text').get('').strip()
        item['Thumbnail'] = response.meta.get('thumbnail_text', '')
        item['Summary'] = response.css('.c-entry-summary ::text').get('')
        item['Image URL'] = main_image_url
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
            columns = data.fieldnames
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
        sheet_range = tab_sheet_name  # Sheet name and range of the cells7

        # append data
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=sheet_range,
            body={
                "majorDimension": "ROWS",
                "values": rows_values  # representing each row values as list. So it contains as list of lists
            },
            valueInputOption="USER_ENTERED"
        ).execute()

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

    def close(spider, reason):
        spider.update_google_sheet()
