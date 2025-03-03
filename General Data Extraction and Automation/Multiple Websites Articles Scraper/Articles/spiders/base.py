import csv
from collections import OrderedDict
from datetime import datetime

from scrapy import Spider, Request

from googleapiclient.discovery import build
from oauth2client.service_account import ServiceAccountCredentials
import gsheets


class BaseSpider(Spider):
    name = "base"

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
        self.output_filename = f'output/{self.name} Articles Scraper.csv'
        self.output_fieldnames = ['Title', 'Summary', 'Image URL', 'Image Text', 'Description HTML', 'Published At',
                                  'Article URL']
        self.chien_headers = ['Title', 'Category', 'Intro', 'Image', 'Source Img', 'Content', 'URL']
        self.tekpolis_headers = ['Title', 'Intro', 'Image', 'Content', 'Category', 'Tags', 'Article URL']
        self.the_blog_headers = ['Title', 'Intro', 'Image', 'Content', 'Category', 'Tags', 'URL']
        self.cleantuesday_headers = ['Category', 'Title', 'Image', 'Content', 'Article URL']
        self.techno_science_headers = ['Category', 'Title', 'Sources', 'Image', 'Content', 'Article URL']
        self.sneakernews_headers = ['Title', 'Intro', 'Main Image', 'Content', 'Images of Shoes', 'Tags', 'Article URL']
        self.enerzine_headers = ['Category', 'Title', 'Intro', 'Image', 'Credits (sources)', 'Tags', 'Article URL']

    def parse(self, response, **kwargs):
        pass

    def parse_detail(self, response):
        pass

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

    def update_google_sheet(self, data):
        if not data:
            self.logger.debug('\n\nThere is no new article found...!!!\n\n')
            return

        columns = [[col for col in row.keys()] for row in data][:1]
        rows_values = [[value for value in row.values()] for row in data]

        if not self.gsheet_scraped_items_urls:
            rows_values = columns + [[value for value in row.values()] for row in data]

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
        spider.write_items_to_csv()

    def get_date_time(self, response):
        date_time = response.css('[property="article:published_time"] ::attr(content)').get('')
        parsed_datetime = datetime.fromisoformat(date_time)
        readable_datetime = parsed_datetime.strftime('%m/%d/%y : %I:%M %p')
        return readable_datetime

    def write_items_to_csv(self, mode='w'):
        if not self.current_scraped_items:
            return

        # fieldname = self.chien_headers if 'chien' in self.current_scraped_items[0].get(
        #     'URL') else self.tekpolis_headers if 'tekpolis' in self.current_scraped_items[0].get('Article URL')  else self.output_fieldnames

        fieldname = self.get_fieldname()
        with open(self.output_filename, mode=mode, newline='', encoding='utf-8') as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldname)

            if csv_file.tell() == 0:
                writer.writeheader()

            writer.writerows(self.current_scraped_items)

    def get_today_date(self):
        date = datetime.now()
        today_date = date.strftime('%Y-%m-%d').lower().strip()
        return today_date

    def get_fieldname(self):
        chien_url = self.current_scraped_items[0].get('URL', '')
        the_blog_url = self.current_scraped_items[0].get('URL', '')
        tekpolis_url = self.current_scraped_items[0].get('Article URL', '')
        cleantuesday_url = self.current_scraped_items[0].get('Article URL', '')
        techno_science_url = self.current_scraped_items[0].get('Article URL', '')
        sneakernews_url = self.current_scraped_items[0].get('Article URL', '')
        enerzine_url = self.current_scraped_items[0].get('Article URL', '')

        if 'chien' in chien_url:
            headers = self.chien_headers
        elif 'tekpolis' in tekpolis_url:
            headers = self.tekpolis_headers
        elif 'the-blog' in the_blog_url:
            headers = self.the_blog_headers
        elif 'cleantuesdayparis' in cleantuesday_url:
            headers = self.cleantuesday_headers
        elif 'techno-science' in techno_science_url:
            headers = self.techno_science_headers
        elif 'sneakernews' in sneakernews_url:
            headers = self.sneakernews_headers
        elif 'enerzine' in enerzine_url:
            headers = self.enerzine_headers
        else:
            headers = self.output_fieldnames

        return headers
