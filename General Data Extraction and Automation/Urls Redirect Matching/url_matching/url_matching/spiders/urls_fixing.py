import csv
import glob
import os
import time
from datetime import datetime

import pandas as pd
import requests
from scrapy import Request, Spider, Selector

import scrapy_xlsx


class UrlsFixingSpider(Spider):
    name = "urls_fixing"

    custom_settings = {
        'CONCURRENT_REQUESTS': 8,

        'FEED_EXPORTERS': {
        'xlsx': 'scrapy_xlsx.XlsxItemExporter',
    },
        'FEEDS': {
            f'output/Amazon Products Reviews {datetime.now().strftime("%d%m%Y%H%M")}.xlsx': {
                'format': 'xlsx',
                # 'fields': ['SKU', 'Title', 'Brand', 'Price', 'Availability', 'Size', 'Color', 'URL']
                'fields': ['#', 'Page title', 'Page URL', 'Language', 'UR', 'Referring domains', 'Top DR', 'Links to target', 'New Links',
                           'Lost Links', 'Dofollow', 'Nofollow', 'Redirects', 'Page HTTP code', 'First seen', 'Last seen']
            }
        },

        'MEDIA_ALLOW_REDIRECTS': True,
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.broken_urls = self.get_filtered_page_urls_from_csv()
        a=1

    def start_requests(self):
        archive_urls = []
        for row in self.broken_urls.itertuples():
            print(row)
            url = row[1]
            url = f"https://archive.org/wayback/available?url=+{url}"

            r = requests.get("https://archive.org/wayback/available?url=" + url)
            archive_urls.append(r.json()['archived_snapshots']['closest']['url'])
            time.sleep(0.2)
            # r = requests.get("https://archive.org/wayback/available?url=" + url)
            yield Request(url=url, callback=self.parse_archive, meta={'page_url': url})

    def parse_archive(self, response):
        a=1
        archive_urls = []
        try:
            archive_urls.append(response.json()['archived_snapshots']['closest']['url'])
            time.sleep(0.2)
        except requests.exceptions.HTTPError as errh:
            print("Http Error:", errh)
        except requests.exceptions.ConnectionError as errc:
            print("Error Connecting:", errc)
        except requests.exceptions.Timeout as errt:
            print("Timeout Error:", errt)
        except requests.exceptions.RequestException as err:
            print("Oops: Something Else", err)
        except KeyError:
            # continue
            a=1
        except ValueError:
            # continue
            a=1
        print(archive_urls)


    def parse(self, response, **kwargs):
        pass

    def get_filtered_page_urls_from_csv(self):
        try:
            # Find the CSV file in the 'input' directory
            file_list = glob.glob('input/*.csv')

            if not file_list:
                print("No CSV file found in the 'input' directory.")
                return None

            file_name = file_list[0]
            print(f"CSV file found: {file_name}")

            # Check if the file exists
            if not os.path.exists(file_name):
                print(f"Error: The file {file_name} does not exist.")
                return None

            # Load CSV and only use 'Page URL' column
            try:
                broken = pd.read_csv(file_name, encoding='utf-8', sep=',', usecols=['Page URL'])
                print("CSV file loaded successfully.")
            except ValueError as ve:
                print(f"Error: {ve}")
                print("Ensure the column 'Page URL' exists in the CSV file.")
                return None

            # Filter out unwanted file types from the URLs
            searchfor = ['xml', 'jpg', 'jpeg', 'gif', 'png', 'svg', 'ico']
            try:
                broken_filtered = broken[~broken['Page URL'].str.contains('|'.join(searchfor), na=False)]
                print(f"Filtered URLs, remaining rows: {len(broken_filtered)}")
            except Exception as e:
                print(f"Error during URL filtering: {e}")
                return None

            # Return the first 5 rows of filtered data
            return broken_filtered.head()

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            return None

