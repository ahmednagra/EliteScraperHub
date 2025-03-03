import csv
import json
import os
import re
from urllib import request
from collections import OrderedDict

import requests
import urllib3
from scrapy import Selector

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class AmazonProductSpider:
    base_url = 'https://www.amazon.com'
    start_urls = ["https://www.amazon.com"]

    custom_settings = {
        'CONCURRENT_REQUESTS': 1,
    }

    def __init__(self, urls, proxy):
        self.urls = urls
        self.proxy = proxy

    def product_detail(self, **kwargs):
        for url in self.urls:
            req = requests.request("GET", url, proxies=self.proxy, verify=False)

            if req.status_code == 200:
                response = Selector(text=req.text)
                product_features = self.get_product_features(response)
                images = self.get_images_links(response)

                item = OrderedDict()
                item['Product Name'] = response.css('#productTitle::text').get('').strip()
                item['Product Details'] = str(product_features).strip() if product_features else ''
                item['Product Information'] = self.get_product_information(response)
                item['Product Videos'] = self.get_videos_link(response)
                item['Url'] = url

                self.write_to_csv(item, images)

    def get_product_features(self, response):
        selectors = response.css('[data-feature-name="productOverview"] div table tr, .product-facts-detail')

        # Product details mean Features
        product_feature = {}
        for selector in selectors:
            key = ', '.join([ele.strip() for ele in selector.css('.a-span3 ::text').getall() if ele.strip()])
            value = ', '.join([ele.strip() for ele in selector.css('.a-span9 span::text').getall() if ele.strip()])
            if key and value:
                product_feature[key.strip()] = value.strip()
            else:
                values = selector.css('span::text').getall()
                values = [ele.replace('\n', '') for ele in values if ele.strip()]
                product_feature[values[0]] = values[1]

        product_feature_str = '\n'.join([f"{key}: {value}" for key, value in product_feature.items()])

        highlights = {}
        high_lights = response.css('#glance_icons_div .a-span6')
        for highlight in high_lights:
            key = highlight.css('span::text').get('').strip()
            value = ''.join(highlight.css('span::text').getall()[-1]).strip()
            if key and value:
                highlights[key.strip()] = value.strip()

        product_highlights_str = '\n'.join([f"{key}: {value}" for key, value in highlights.items()])

        # About this item Section
        about_selector = response.css('#featurebullets_feature_div #feature-bullets, #productFactsDesktop_feature_div')
        about_section = []
        title = about_selector.css('hr + ::text').get('') or about_selector.css('h1::text, h3::text').get('')
        about_section.append(title)

        about_text = about_selector.css('ul ::text').getall()
        about_text = '\n'.join([ele.strip() for ele in about_text if ele.strip()])
        about_section.append(about_text)

        about_section = '\n'.join(about_section)

        info = '\n\n'.join(
            filter(None, [product_feature_str.strip(), product_highlights_str.strip(), about_section.strip()]))

        return info

    def get_images_links(self, response):
        try:
            # Extracting images data from script tag
            images_json_str = response.css('script[type="text/javascript"]:contains(ImageBlockATF)').re_first(
                f"'colorImages':(.*)").rstrip(',').replace("'", '"')

            # Parsing JSON data
            images_json = json.loads(images_json_str) if images_json_str else {}

            # Accessing the list of images
            images_list = images_json.get('initial', [])
        except (json.JSONDecodeError, AttributeError) as e:
            print('Error Parsing script tag For images url : ', e)
            images_list = []

        # Extracting full-size images URLs from the main slider
        full_size_images_urls = [item.get('hiRes', '') for item in images_list]
        images_urls = [url for url in response.css(
            '.regularAltImageViewLayout .a-list-item .a-button-text img::attr(src)').getall() if
                       'images-na.ssl' not in url] or []

        # images_urls = [re.sub(r'\._.*', '._AC_SX522_.jpg', url) for url in images_urls]
        images_urls = [re.sub(r'\._.*', '._AC_SL1500_.jpg', url) for url in images_urls]

        # Extracting product description images
        product_description_images = response.css(
            '.aplus-v2.desktop.celwidget img[src*=media-amazon]::attr(src)').getall()
        product_description_images = [re.sub(r'\._.*', '._AC_SL1500_.jpg', url) for url in product_description_images]

        # Combining full-size images URLs and product description images
        if full_size_images_urls and product_description_images:
            full_size_images_urls.extend(product_description_images)
        else:
            images_urls.extend(product_description_images)

        # Returning the combined list of images URLs
        return full_size_images_urls or images_urls

    def get_videos_link(self, response):
        video_selector = response.css('.a-carousel a.vse-desktop-carousel-card::attr(href)').getall()

        if not video_selector:
            return ''

        # Replace '/vdp' with 'https://www.amazon.com/live/video' in each URL
        urls = [video.replace('/vdp', 'https://www.amazon.com/live/video') for video in video_selector]

        return ','.join(urls)

    def get_product_information(self, response):
        product_information = {}

        rows = response.css('#productDetails_techSpec_section_1 tr') or response.css(
            '.content-grid-block table tr') or ''
        if not rows:
            product_details = response.css('.detail-bullet-list li:not(:has(script))')

        else:
            product_details = []

        for row in rows:
            key = row.css('th::text').get('') or row.css('td strong::text').get('')
            value = row.css('td p::text').get('') or row.css('td::text').get('')
            if key and value:
                value = value.replace('\u200e', '')
                value = ' '.join(value.strip().split())
                product_information[key.strip()] = value

        for detail in product_details:
            key = detail.css('.a-text-bold::text').get('').strip()
            value = detail.css('.a-text-bold + span::text').get('')
            if key and not value:
                if not detail.css('script'):
                    value = ''.join(detail.css('li ::text').getall()).strip()
                    value = value.replace(key, '').strip()
                else:
                    value_selector = detail.css('li span:contains("stars")::text').getall()
                    value = ''.join([val for val in value_selector if val.strip()])
            # if key and value:
            if key:
                key = key.replace(':', '').replace('\u200e', '').replace(' \u200f', '')
                key = ' '.join(key.strip().split())
                value = value.replace('\u200e', '')
                value = ' '.join(value.strip().split())
                product_information[key] = value

        additional_information = response.css('#productDetails_detailBullets_sections1 tr') or ''

        for row in additional_information:
            key = row.css('th::text').get('')
            value = ' '.join(row.css('td *::text').getall()).strip()
            if key and value:
                value = value.split('\n')[-1].strip()
                product_information[key.strip()] = value
        if product_information:
            # Dictionary to String Convert
            product_information = '\n'.join([f"{key}: {value}" for key, value in product_information.items()])
            return product_information
        else:
            return ''

    def write_to_csv(self, item, images):
        try:
            # Extract ASIN from the URL
            asin = item.get('Url', '').split('dp/')[1].split('?')[0]
            asin = asin.strip('/')

            # Define the product folder path using ASIN
            product_folder = os.path.join('output', asin)
            os.makedirs(product_folder, exist_ok=True)

            # Create the image folder
            image_folder = os.path.join(product_folder, 'images')
            os.makedirs(image_folder, exist_ok=True)

            # Download and save images
            for index, image_url in enumerate(images):
                image_name = f'image_{index + 1}.jpg'
                image_path = os.path.join(image_folder, image_name)
                request.urlretrieve(image_url, image_path)

            # Write item data to CSV file
            csv_filename = os.path.join(product_folder, f'{asin}.csv')
            with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = list(item.keys())
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow(item)
            print('Product Successfully scraped and saved')

        except Exception as e:
            print(f"An error occurred: {str(e)}")


def read_input_urls_from_file(file_path):
    try:
        with open(file_path, mode='r') as txt_file:
            return [line.strip() for line in txt_file.readlines() if line.strip()]

    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return []
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return []


if __name__ == '__main__':
    # Read URLs and proxy information from text files
    urls = read_input_urls_from_file('input/urls.txt')
    proxy_token = read_input_urls_from_file('input/proxy_key.txt')
    proxyModeUrl = "http://{}:@proxy.scrape.do:8080".format(''.join(proxy_token))
    proxy = {
        "http": proxyModeUrl,
        "https": proxyModeUrl,
    }

    # Instantiate the spider with URLs and proxy
    spider = AmazonProductSpider(urls, proxy)

    # Start the requests
    spider.product_detail()
