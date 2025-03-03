import scrapy
import pandas as pd
from urllib.parse import quote
import re
from datetime import datetime
import csv
import os
import glob



class PeopleSpiderSpider(scrapy.Spider):
    name = "people_spider"

    def start_requests(self):
        # Get the directory containing the current script
        script_dir = os.path.dirname(os.path.abspath(__file__))

        project_dir = os.path.abspath(os.path.join(script_dir, '..'))

        # Define the path to the input folder
        input_folder = os.path.join(project_dir, 'input')

        # Get the list of .xlsx files in the folder
        xlsx_files = glob.glob(os.path.join(input_folder, '*.xlsx'))

        # Assign the first file to file_path if it exists
        file_path = xlsx_files[0] if xlsx_files else None
        if file_path:
            if not os.path.exists('output'):
                os.makedirs('output')
            csv_file = f'output/truepeopleData_{datetime.now().timestamp()}.csv'

            # Load addresses and zip codes from the Excel file
            df = pd.read_excel(file_path)

            # Prepare the CSV file with headers and rows for each address
            self.prepare_csv(csv_file, df)
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Origin': 'https://www.truepeoplesearch.com',
                'Referer': 'https://www.truepeoplesearch.com/',
                'Upgrade-Insecure-Requests': '1',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
                'sec-ch-ua-arch': '"x86"',
                'sec-ch-ua-bitness': '"64"',
                'sec-ch-ua-full-version': '"131.0.6778.86"',
                'sec-ch-ua-full-version-list': '"Google Chrome";v="131.0.6778.86", "Chromium";v="131.0.6778.86", "Not_A Brand";v="24.0.0.0"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-model': '""',
                'sec-ch-ua-platform': '"Windows"',
                'sec-ch-ua-platform-version': '"15.0.0"',
            }

            for index, row in df.iterrows():
                address = row.get('Owner Mailing Address', '').strip()
                zip_code = row.get('Owner Mailing Zip', '')

                if address and zip_code:
                    formatted_address = quote(address)
                    url = f'https://www.truepeoplesearch.com/resultaddress?streetaddress={formatted_address}&citystatezip={zip_code}'
                    yield scrapy.Request(url, callback=self.parse, headers=headers, meta={
                        "zyte_api": {"geolocation": "US", "browserHtml": True},
                        'referer': url,
                        'csv_file': csv_file,
                        'address': address
                    })
        else:
            print('No Xlsx file found in the input folder')

    def parse(self, response):
        address = response.meta.get('address')
        referer = response.meta.get('referer')
        csv_file = response.meta.get('csv_file')
        detail_page_links = response.css('.card-summary::attr(data-detail-link)').getall()
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'no-cache',
            # 'cookie': 'pxcts=51e3a95e-ac35-11ef-b60c-5bdcf2377ebd; _pxvid=51e39e57-ac35-11ef-b60c-e0d63cc616e1; _ga=GA1.1.1119016643.1732653058; _lr_env_src_ats=false; cto_bundle=54Kg819mS2lrUVBpRVklMkJURWs0bDJRNW1uWmZsQTVPVW5IVCUyQnU5cWxCMWpZUnlBdG9qMmJOZW1zZXYzdGtreVRLNnAwMVBFa29MZFMweXBJRDRaNU16UnhyemdseHAya0gxeUZKcUYlMkJpMVZlNFpRaG5LM1pkNDQ3NiUyRk00SUJZUUw0QjNCZ0E3TFFsWDJha1Q4Q0xJOXBrU0dLMDdpJTJGUk1BYzY4Z285djh1aHR3YUNua1NJYmNQMzI5VHNsU1YlMkZVdnlKclQxeFB6aXE2a1ZvbE5DTW53MWY2JTJCaFElM0QlM0Q; _cc_id=fe40aabd5f172c65d6a66494eaf332ca; panoramaId=5594574d1bc9e78a49d611bbed6b16d5393877863bd2a59d3371c9d8427a368c; panoramaIdType=panoIndiv; panoramaId_expiry=1733257967763; _clck=5m8r1p%7C2%7Cfr7%7C0%7C1791; __qca=P0-1918307079-1732653191850; _au_1d=AU1D-0100-001732653438-N9YAS7PZ-71A2; TiPMix=95.34102597745515; x-ms-routing-name=self; _lr_retry_request=true; __gads=ID=f663369b996dfcc2:T=1732653066:RT=1732658289:S=ALNI_MZ41nFHEGk12y896WT6ddl-JPa5pw; __gpi=UID=00000db3a4e30e31:T=1732653066:RT=1732658289:S=ALNI_MZl8cHlo3QRNCdUo9BVf_jVgMpsig; __eoi=ID=3736e2d30e3974c6:T=1732653066:RT=1732658289:S=AA-AfjaoJ5SFyPnIxV5_Grg7Y0O9; FCNEC=%5B%5B%22AKsRol80KbVtrI8KL2Ca-vXR1eTE_nZRrdyYAQR-8B2MxGPenoC0tT5ZqGUAKGQuC3Pa6G7ySvwL72cujxEhuXmtgskMaY4yyk89rzFaGUuRh_LGGpI2k4_G96hf3nw0A36WdSeYt72L9rbc9hT7V98F0vEOU1Yn9w%3D%3D%22%5D%5D; cf_clearance=FAKiCNfv9.xKB79XN8CZ0P06ViH8Os_ppWP1cZ9f0hU-1732659452-1.2.1.1-PLQQtb6E1Owu2SSt4ThS_wxwYYru0Z_8K24Gta7ASjGnbxnckdTJkPv13wfOXf3l0gHbcuwD82jSa1tHJZuG66QVumrBFfIBKxovm4W_ryN6dVoyM2VsoPa2bwVXkcxLdOddWAqzzN7qL8p2IYuL6_8fF5dX2kskiShI01TuGiNIuBFWQIkrrh9oHI2e.Hks_8gwIPjNlMShKElnA5t5wuWBhoW2Y50j_KWf.TNdF41hrQHVAItOCGjeEFB.NU45VNZ1s45kQIuJD6ddjKqPMkLo9fwz7TfbvAqIo9BLWuuM6QPDmMdmDK8zcyCWjyjv1jC7HNQaCW1U8xE3o6aONZc11OrFs8nDRgv_P4nqIWWDFY3sH0lqVRGXffRmQU2.; _px3=3fcb58471696083bf46d8e564828b1408df674f7af7255b2dbbf7dccf964480f:MP8B1Hu8NdHtgLQ+K1duGA6VlL0ZQA2B6t6JZoimcWWh3lYJCGVrLtiEIoMCSqWwjdOMyKPBJ/9GM270n6wuHQ==:1000:k8Sx1whasc+6D5gaQ72HCQ8SFX8n8Ny/JBBZ4OSVDY2Dz+L24YFwZy7eRZxhpaVfGSbgWSoOgj/sdu+3yecPmD6dWolMhWwbHUOH2NxmNwvjYoK9UpJutrXcuZhImDcfuzfKc+55yTA7ZfISek9lhUz0pVeA8P1Ro/ZHZWuPq4mcGOfaFumcQlilm9cFjof+bL3UkZuLjRNGGL8cd7/65m5J3n0GG8Ju2o9NKSgyoqw=; _clsk=1ha0q2d%7C1732661197973%7C4%7C0%7Cd.clarity.ms%2Fcollect; __cf_bm=JKPieG9B4XaV4UfnE5l1JkHctVCnRVxCR0zGMNdC8yI-1732661214-1.0.1.1-vXfzGKln3IKN884zOnLjt5SJ2qAWZiM4P3JOZsXQJThhv9L7qKp520.2rEKfTTnRXu62Ncc_piFYb.NvZdOekQ; _ga_JB1DKYFLTX=GS1.1.1732658289.2.1.1732661219.0.0.0',
            'pragma': 'no-cache',
            'priority': 'u=0, i',
            'referer': referer,
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'service-worker-navigation-preload': 'true',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
        }
        # Limit to 5 detail links
        if len(detail_page_links) > 5:
            detail_page_links = detail_page_links[:5]

        for i, link in enumerate(detail_page_links, start=1):
            link = 'https://www.truepeoplesearch.com' + link
            yield scrapy.Request(link, callback=self.detail_page, headers=headers, meta={
                "zyte_api": {"geolocation": "US", "browserHtml": True},
                'person_no': i,
                'csv_file': csv_file,
                'address': address
            })

    def detail_page(self, response):
        address = response.meta.get('address')
        csv_file = response.meta.get('csv_file')
        person_no = response.meta.get('person_no')

        # Extract data
        full_name = response.css('.oh1::text').get()
        birth_info = response.css('.oh1 +.d-sm-none+span::text').get()
        p_city = response.css('[itemprop="addressLocality"]::text').get()
        p_state = response.css('[itemprop="addressRegion"]::text').get()
        p_zip = response.css('[itemprop="postalCode"]::text').get()
        age = None

        if birth_info:
            # Try to match "Age <number>" pattern
            age_match = re.search(r'Age\s+(\d+)', birth_info)
            if age_match:
                age = int(age_match.group(1))
            else:
                # Try to match "(age <number>)" pattern
                match = re.search(r'\(age (\d+)\)', birth_info)
                if match:
                    age = int(match.group(1))

        current_address = response.css('[itemprop="streetAddress"]::text').get()
        if current_address:
            current_address = f"{current_address}, {p_city} {p_state} {p_zip}"
        p_location = f"{p_city}, {p_state}"
        all_phone = response.css('[data-link-to-more="phone"] [itemprop="telephone"]::text').getall()
        if len(all_phone) > 5:
            all_phone = all_phone[:5]

        # Prepare row data
        row_data = {
            f'Person {person_no} Name': full_name,
            f"Person {person_no} Age": age,
            f"Person {person_no} location": p_location,
            f"Person {person_no} currentAddress": current_address,
        }
        for index, phone in enumerate(all_phone, start=1):
            row_data[f"Person {person_no} phone {index}"] = phone

        # Write data to the matching row in the CSV file
        self.update_csv(address, row_data, csv_file)


    def prepare_csv(self, csv_file, df):
        """Prepare the CSV file with predefined headers and rows for addresses."""
        headers = [
                      "Address", "City", "State", "Zip", "Owner 1 First Name", "Owner 1 Last Name",
                      "Owner 2 First Name", "Owner 2 Last Name", "Owner Mailing Address", "Owner Mailing City",
                      "Owner Mailing State", "Owner Mailing Zip", "searchedAddress"
                  ] + [
                      f"Person {i} {field}"
                      for i in range(1, 6)
                      for field in ["Name", "Age", "location", "currentAddress"] + [f"phone {j}" for j in range(1, 6)]
                  ]

        # Write headers and empty rows for each address
        with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=headers)
            writer.writeheader()
            for _, row in df.iterrows():
                address = row.get('Address', '').strip()
                zip_code = row.get('Zip', '')
                city = row.get('City', '')
                state = row.get('State', '')
                owner_1_first_name = row.get('Owner 1 First Name', '')
                owner_1_last_name = row.get('Owner 1 Last Name', '')
                owner_2_first_name = row.get('Owner 2 First Name', '')
                owner_2_last_name = row.get('Owner 2 Last Name', '')
                owener_mailing_address = row.get('Owner Mailing Address', '')
                owner_mailing_city = row.get('Owner Mailing City', '')
                owner_mailing_state = row.get('Owner Mailing State', '')
                owner_mailing_zip = row.get('Owner Mailing Zip', '')
                searchAddress = owener_mailing_address + ' , ' + owner_mailing_city + ' ' + owner_mailing_state
                if owener_mailing_address and owner_mailing_zip:
                    writer.writerow({"Address": address, "Zip": zip_code, "City": city, "State": state, "Owner 1 First Name": owner_1_first_name,
                    "Owner 1 Last Name": owner_1_last_name, "Owner 2 First Name": owner_2_first_name, "Owner 2 Last Name": owner_2_last_name,
                    "Owner Mailing Address": owener_mailing_address, "Owner Mailing City": owner_mailing_city, "Owner Mailing State": owner_mailing_state,
                    "Owner Mailing Zip": owner_mailing_zip, "searchedAddress": searchAddress})

    def update_csv(self, address, data, csv_file):
        """Update the row in the CSV file matching the address."""
        temp_file = csv_file + ".tmp"
        updated = False

        with open(csv_file, mode='r', newline='', encoding='utf-8') as infile, \
                open(temp_file, mode='w', newline='', encoding='utf-8') as outfile:
            reader = csv.DictReader(infile)
            writer = csv.DictWriter(outfile, fieldnames=reader.fieldnames)
            writer.writeheader()

            for row in reader:
                if row["Owner Mailing Address"] == address:
                    row.update(data)
                    updated = True
                writer.writerow(row)

        os.replace(temp_file, csv_file)

        # Log if the row was not found
        if not updated:
            self.logger.warning(f"No matching row found for address: {address}")
