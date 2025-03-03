import os
import glob
import re
import csv
import json
from math import ceil
from collections import OrderedDict
from datetime import datetime, timedelta

import requests
import airtable
from pyairtable import Api, Workspace, models, Table
from pyairtable.models import schema, Collaborator
from scrapy import Request, Spider, FormRequest


class AirtableDataSpider(Spider):
    name = 'ini_airtable'
    base_url = 'www.airtable.com'
    start_urls = ['https://www.airtable.com']
    current_dt = datetime.now().strftime('%d%m%Y%H%M')

    custom_settings = {
        'CONCURRENT_REQUESTS': 4,
        'RETRY_TIMES': 5,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408],
    }
    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9',
        # 'cache-control': 'no-cache',
        'content-type': 'application/x-www-form-urlencoded',
        # 'cookie': 'brw=brwvCHSV81kVXQTfm; pxcts=9f7814cb-1114-11ef-a4a7-e3bc9df4474a; _pxvid=9f7806e7-1114-11ef-a4a7-7319b1932ce3; _ga=GA1.1.1200310951.1715596577; mv=eyJzdGFydFRpbWUiOiIyMDI0LTA1LTEzVDEwOjM5OjQ0LjUwMVoiLCJsb2NhdGlvbiI6Imh0dHBzOi8vYWlydGFibGUuY29tL2FwcFJaR2ZydzBaSTdUZjJQLyoqKioqKioqKioqKioqKioqIiwiaW50ZXJuYWxUcmFjZUlkIjoidHJjY0xBblJnbEpQQldMS0YifQ==; ff_performance=%7B%22contentSecurityPolicyBlockingMode%22%3A%22treatment%22%7D; ff_targeting=%7B%22genericMarketingABTest%22%3A%22treatment%22%2C%22genericMarketingMultivariateTest%22%3A%22control%22%2C%22marketingHomePageABTest%22%3A%22control%22%2C%22marketingMultivariateHomePageTest%22%3A%22control%22%7D; _gcl_au=1.1.778444145.1715598510; _uetsid=24dd20b0111911ef8ab8070c6592d0a9; _uetvid=24de1030111911ef8fb94327a0ffe2d2; _hly_vid=6762f009-f71f-4c3a-9506-a4ab4ea6c3e8; AWSALBAPP-0=_remove_; AWSALBAPP-1=_remove_; AWSALBAPP-2=_remove_; AWSALBAPP-3=_remove_; _ga_HF9VV0C1X2=GS1.1.1715599834.1.0.1715599834.60.0.0; lithiumSSO:=~2RBZq0bb03z3yoPNc~c9ThqXaWz4T5O12pJAA3R3RMr_07LPVEAE7yLtbteIVIk84D0F8-2HiIEJZbcFLY6hUKVjGfBNLadabff7FEKUDyfcHwoRaCG9zOveTwfTzOog55-SO9oc9DAxW1mUliz_0OlokyDThug6WhyAi6VBPv_kSaFspQnr2LwMK0FutoTizTQnuP9_4Cv-5MVfS3I9GyNWt3JGSGVPePmWTLmUl58SpE6oNEdNgHEkmhM1PgZC2poN90J9YEMVbylaju95HBi7fmfQ9WLb9uRy7NoeRF6Ho-6JLRrxvsQD2ODn2UJPlLDQvZ4SHbarYcgMui0kTQ4vhXPfToTJmm-q3z6g..; acq=eyJhY3F1aXNpdGlvbiI6Ilt7XCJwbGF0Zm9ybVwiOlwiZGVza3RvcFwiLFwib3JpZ2luXCI6XCJzaWdudXBcIixcInRvdWNoVGltZVwiOlwiMjAyNC0wNS0xM1QxMTozNDozMC45NTJaXCJ9LHtcInBsYXRmb3JtXCI6XCJkZXNrdG9wXCIsXCJvcmlnaW5cIjpcImxvZ2luXCIsXCJ0b3VjaFRpbWVcIjpcIjIwMjQtMDUtMTNUMTE6MzU6MjAuODc0WlwifV0iLCJyZWRpcmVjdFRvQWZ0ZXJMb2dpbiI6Ii9hcHBSWkdmcncwWkk3VGYyUC90Ymx2S2ZLZW9jZjF6YWE2ci92aXc0YU9rc3ZaaUNod1h0cj9ibG9ja3M9aGlkZSJ9; acq.sig=VZLuTFnmNSx5OYsOieDsGcj9vyfa_6Y-E6lSScfphJ8; __Host-airtable-session=eyJzZXNzaW9uSWQiOiJzZXNHbTc0MVdId1p5QkpiYSIsImNzcmZTZWNyZXQiOiJ6a0xMY3F4VUxVZURRQlZHam12eGQzenEifQ==; __Host-airtable-session.sig=PjxdpnHzC-RHObn-ntatDVM5jtk0a6siV6zByDRwRbo; OptanonConsent=isGpcEnabled=0&datestamp=Mon+May+13+2024+16%3A35%3A36+GMT%2B0500+(Pakistan+Standard+Time)&version=202308.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=ea0be97d-d0d2-498a-baee-8fa8121abc68&interactionCount=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0007%3A1%2CC0003%3A1%2CC0004%3A1&AwaitingReconsent=false&isAnonUser=1; AWSALB=0eNL+nwneww2dxARqXn4f+85Vg/ZWF40OuQcF0HI4MMezedBtUOhkHjt+UbUFm7u/0WhVefx2u0Z04/33F5wXZMPyTu/0BsY4WUqGHposIjlo9mytBP3uMWgAu7r; AWSALBCORS=0eNL+nwneww2dxARqXn4f+85Vg/ZWF40OuQcF0HI4MMezedBtUOhkHjt+UbUFm7u/0WhVefx2u0Z04/33F5wXZMPyTu/0BsY4WUqGHposIjlo9mytBP3uMWgAu7r; mbpg=2025-05-13T11:36:14.016ZusrokZnv4AGZxvfI7pro; mbpg.sig=wBzMPfW1Zcblix5gj4sIBkr6Sbgac-DGhyMktH8cEUY; _px3=0f39a0d15217b594dce90903bab0bfaba0e255818206b6e4f89cce02c1a36726:4dq/6lqr8Ti6e1w3F/KCSH7cMsfUTsbnom85yWg52kGNC6i8D1ZnN1wC8nrL9goqBmWSwcluqvnznHZHQmlwjA==:1000:4Rr0voDLWhT1nBNGmqpbwlXojPO3dNC+fDUeCEbKwGmLAeEpboaL4dsxHuKfhYBdSl/I3Gxu9yqLSGz4DdClCTbRJ0Q97j87TGagc6xs+5r4El3yQ0KSsOnTfZzhCllFlnL9D//wvwr5oB6zhS0tEIEJE3j+RyQ7X6aBUZ6qpaC8xQS0LnlWsqIdBIpNxw3KI4jzFzP4CuHRd+6PIowVhuB0vSix4SqandH+EQPPgWk=; _ga_VJY8J9RFZM=GS1.1.1715596577.1.1.1715600668.60.0.0',
        # 'origin': 'https://airtable.com',
        # 'pragma': 'no-cache',
        'priority': 'u=0, i',
        # 'referer': 'https://airtable.com/login',
        # 'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        # 'sec-ch-ua-mobile': '?0',
        # 'sec-ch-ua-platform': '"Windows"',
        # 'sec-fetch-dest': 'document',
        # 'sec-fetch-mode': 'navigate',
        # 'sec-fetch-site': 'same-origin',
        # 'sec-fetch-user': '?1',
        # 'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.api_token = 'pat3nmkWdDAV006vL.a5fe37f3419663e5351f78ca9d88938df03ce3c52c8e1c5cc4819e9b58697587'
        self.workspace_id = 'wspkHKNrPBF3B6V3N'
        self.logs_filepath = f'logs/logs {self.current_dt}.txt'
        self.username = ''
        self.password = ''
        self.records = self.read_input_data_from_json()
        self.error = []
        self.mandatory_logs = [f'Spider "{self.name}" Started at "{self.current_dt}"\n']

        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json',
        }

    def start_requests(self):
        api = Api(self.api_token)

        # Get user info
        user_info = api.whoami()

        # All Bases Info
        bases_info = {}
        bases = api.bases()  # Adjust this if there's a specific method to get all bases
        for base in bases:
            bases_info[base.name] = base.id

        # tables records in the specific Base
        if bases_info:
            for base_name, base_id in bases_info.items():
                url = f'https://api.airtable.com/v0/meta/bases/{base_id}/tables'
                base_detail = requests.get(url, headers=self.headers)
                tables_info = {}
                if base_detail.status_code == 200:
                    for table in base_detail.json().get('tables', [{}]):
                        tables_info[table.get('name', '')] = table.get('id', '')

        # create Table Code
        create_table_url = f'https://api.airtable.com/v0/meta/bases/appcLQ4N9gSKf98ly/tables'
        create_table_req = requests.request(method='POST', url=create_table_url, headers=self.headers,
                                            data=json.dumps(self.create_table_data_headers(table_name=self.name)))
        previous_program_ids = []
        if create_table_req.status_code == 200:
            print("Table created successfully")
        else:
            print(f"Error: {create_table_req.content}")
            # download all records from airtable
            # table = api.table('appcLQ4N9gSKf98ly', table_name=self.name)
            # all_records = table.all()
            # previous_program_ids = [record.get('fields', [{}]).get('Program ID', '') for record in all_records]

            previous_program_ids = self.get_previous_records_airtable(api, table_name=self.name)

        # Step 2: Insert records into the table

        # insert_records_url = f'https://api.airtable.com/v0/appcLQ4N9gSKf98ly/{self.name}/'
        #
        # # check the current records already exist on airtable or not
        # insert_records_ids = [row for row in self.records if row.get('Program ID') not in previous_program_ids]
        #
        # # limit of upload records are 10 so make batches of 10 records per batch
        # batches = [insert_records_ids[i:i + 10] for i in range(0, len(insert_records_ids), 10)]
        # for batch in batches:
        #     insert_records_data = {"records": [{"fields": record} for record in batch]}
        #     insert_records_req = requests.request(method='POST', url=insert_records_url, headers=headers,
        #                                           data=json.dumps(insert_records_data))
        # insert_records = self.insert_records_airtable(table_name=self.name, previous_program_ids)


            # if insert_records_req.status_code == 200:
            #     print(f"{len(insert_records_data.get('records'))} :Records inserted successfully")
            # else:
            #     print(f"Error: {insert_records_req.content}")

        a = 1

    def parse(self, response, **kwargs):
        # csrf_token = json.loads(response.css('script:contains("csrfToken") ::text').re_first(r'= (.*)')).get('csrfToken', '')
        data_dict = json.loads(response.css('script:contains("csrfToken") ::text').re_first(r'= (.*)'))
        csrf_token = data_dict.get('csrfToken', '')
        browser_id = data_dict.get('browserId', '')
        form_data = self.get_formdata(csrf_token)
        cookies = self.get_cookies(browser_id)
        url = 'https://airtable.com/auth/login/'
        # yield FormRequest(url=url, formdata=form_data, headers=self.headers)
        reqs = requests.post(url, headers=self.headers, data=form_data, cookies=cookies)
        session = requests.Session()
        session.cookies.update(reqs.cookies)

        home_page = session.get(url='https://airtable.com/')

        pass

    def get_user_cred(self):
        credentials = {}
        with open('input/user_credentials.txt', mode='r', encoding='utf-8') as txt_file:
            for line in txt_file:
                key, value = line.strip().split('==')
                credentials[key.strip()] = value.strip()
        return credentials

    def get_formdata(self, csrf_token):
        self.username = self.get_user_cred().get('user_name', '')
        self.password = self.get_user_cred().get('password', '')
        csrf_token = 'AzBc2yba-OzI4o8S9HUTdjWP_vc9n7gfmUDs'
        # data = {
        #     '_csrf': 'AzBc2yba-OzI4o8S9HUTdjWP_vc9n7gfmUDs',
        #     'email': 'ahmednagra9@gmail.com',
        #     'password': 'Aa7409120',
        # }
        data = {
            '_csrf': csrf_token,
            'email': self.username,
            'password': self.password,
        }

        return data

    def get_cookies(self, brw):
        cookies = {
            # 'brw': 'brwvCHSV81kVXQTfm',
            'brw': brw,
            'pxcts': '9f7814cb-1114-11ef-a4a7-e3bc9df4474a',
            '_pxvid': '9f7806e7-1114-11ef-a4a7-7319b1932ce3',
            '_ga': 'GA1.1.1200310951.1715596577',
            'mv': 'eyJzdGFydFRpbWUiOiIyMDI0LTA1LTEzVDEwOjM5OjQ0LjUwMVoiLCJsb2NhdGlvbiI6Imh0dHBzOi8vYWlydGFibGUuY29tL2FwcFJaR2ZydzBaSTdUZjJQLyoqKioqKioqKioqKioqKioqIiwiaW50ZXJuYWxUcmFjZUlkIjoidHJjY0xBblJnbEpQQldMS0YifQ==',
            'ff_performance': '%7B%22contentSecurityPolicyBlockingMode%22%3A%22treatment%22%7D',
            'ff_targeting': '%7B%22genericMarketingABTest%22%3A%22treatment%22%2C%22genericMarketingMultivariateTest%22%3A%22control%22%2C%22marketingHomePageABTest%22%3A%22control%22%2C%22marketingMultivariateHomePageTest%22%3A%22control%22%7D',
            '_gcl_au': '1.1.778444145.1715598510',
            '_uetsid': '24dd20b0111911ef8ab8070c6592d0a9',
            '_uetvid': '24de1030111911ef8fb94327a0ffe2d2',
            '_hly_vid': '6762f009-f71f-4c3a-9506-a4ab4ea6c3e8',
            'AWSALBAPP-0': '_remove_',
            'AWSALBAPP-1': '_remove_',
            'AWSALBAPP-2': '_remove_',
            'AWSALBAPP-3': '_remove_',
            '_ga_HF9VV0C1X2': 'GS1.1.1715599834.1.0.1715599834.60.0.0',
            'lithiumSSO:': '~2RBZq0bb03z3yoPNc~c9ThqXaWz4T5O12pJAA3R3RMr_07LPVEAE7yLtbteIVIk84D0F8-2HiIEJZbcFLY6hUKVjGfBNLadabff7FEKUDyfcHwoRaCG9zOveTwfTzOog55-SO9oc9DAxW1mUliz_0OlokyDThug6WhyAi6VBPv_kSaFspQnr2LwMK0FutoTizTQnuP9_4Cv-5MVfS3I9GyNWt3JGSGVPePmWTLmUl58SpE6oNEdNgHEkmhM1PgZC2poN90J9YEMVbylaju95HBi7fmfQ9WLb9uRy7NoeRF6Ho-6JLRrxvsQD2ODn2UJPlLDQvZ4SHbarYcgMui0kTQ4vhXPfToTJmm-q3z6g..',
            'acq': 'eyJhY3F1aXNpdGlvbiI6Ilt7XCJwbGF0Zm9ybVwiOlwiZGVza3RvcFwiLFwib3JpZ2luXCI6XCJzaWdudXBcIixcInRvdWNoVGltZVwiOlwiMjAyNC0wNS0xM1QxMTozNDozMC45NTJaXCJ9LHtcInBsYXRmb3JtXCI6XCJkZXNrdG9wXCIsXCJvcmlnaW5cIjpcImxvZ2luXCIsXCJ0b3VjaFRpbWVcIjpcIjIwMjQtMDUtMTNUMTE6MzU6MjAuODc0WlwifV0iLCJyZWRpcmVjdFRvQWZ0ZXJMb2dpbiI6Ii9hcHBSWkdmcncwWkk3VGYyUC90Ymx2S2ZLZW9jZjF6YWE2ci92aXc0YU9rc3ZaaUNod1h0cj9ibG9ja3M9aGlkZSJ9',
            'acq.sig': 'VZLuTFnmNSx5OYsOieDsGcj9vyfa_6Y-E6lSScfphJ8',
            '__Host-airtable-session': 'eyJzZXNzaW9uSWQiOiJzZXNHbTc0MVdId1p5QkpiYSIsImNzcmZTZWNyZXQiOiJ6a0xMY3F4VUxVZURRQlZHam12eGQzenEifQ==',
            '__Host-airtable-session.sig': 'PjxdpnHzC-RHObn-ntatDVM5jtk0a6siV6zByDRwRbo',
            'OptanonConsent': 'isGpcEnabled=0&datestamp=Mon+May+13+2024+16%3A35%3A36+GMT%2B0500+(Pakistan+Standard+Time)&version=202308.2.0&browserGpcFlag=0&isIABGlobal=false&hosts=&consentId=ea0be97d-d0d2-498a-baee-8fa8121abc68&interactionCount=1&landingPath=NotLandingPage&groups=C0001%3A1%2CC0002%3A1%2CC0007%3A1%2CC0003%3A1%2CC0004%3A1&AwaitingReconsent=false&isAnonUser=1',
            'AWSALB': '0eNL+nwneww2dxARqXn4f+85Vg/ZWF40OuQcF0HI4MMezedBtUOhkHjt+UbUFm7u/0WhVefx2u0Z04/33F5wXZMPyTu/0BsY4WUqGHposIjlo9mytBP3uMWgAu7r',
            'AWSALBCORS': '0eNL+nwneww2dxARqXn4f+85Vg/ZWF40OuQcF0HI4MMezedBtUOhkHjt+UbUFm7u/0WhVefx2u0Z04/33F5wXZMPyTu/0BsY4WUqGHposIjlo9mytBP3uMWgAu7r',
            'mbpg': '2025-05-13T11:36:14.016ZusrokZnv4AGZxvfI7pro',
            'mbpg.sig': 'wBzMPfW1Zcblix5gj4sIBkr6Sbgac-DGhyMktH8cEUY',
            '_px3': '0f39a0d15217b594dce90903bab0bfaba0e255818206b6e4f89cce02c1a36726:4dq/6lqr8Ti6e1w3F/KCSH7cMsfUTsbnom85yWg52kGNC6i8D1ZnN1wC8nrL9goqBmWSwcluqvnznHZHQmlwjA==:1000:4Rr0voDLWhT1nBNGmqpbwlXojPO3dNC+fDUeCEbKwGmLAeEpboaL4dsxHuKfhYBdSl/I3Gxu9yqLSGz4DdClCTbRJ0Q97j87TGagc6xs+5r4El3yQ0KSsOnTfZzhCllFlnL9D//wvwr5oB6zhS0tEIEJE3j+RyQ7X6aBUZ6qpaC8xQS0LnlWsqIdBIpNxw3KI4jzFzP4CuHRd+6PIowVhuB0vSix4SqandH+EQPPgWk=',
            '_ga_VJY8J9RFZM': 'GS1.1.1715596577.1.1.1715600668.60.0.0',
        }
        return cookies

    def get_create_table_data(self):
        data = [
            {
                'agmnt_id': 'AE524612',
                'agmnt_title': 'Bidfood Mackay - Enterprise Agreement 2024',
                'matter_no': 'AG2024/666',
                'expiry_date': '01 March 2027',
                'approval_date': '14 May 2024',
                'company_name abn': '88009966465',
                'industry': 'Storage services',
                'storage_name': 'ae524612.pdf',
                'party_name': 'United Imports & Exports Co Pty Ltd',
                'agmnt_type': 'Single-enterprise Agreement'
            },
            {
                'agmnt_id': 'AE524605',
                'agmnt_title': 'Applus+ Pty Ltd Maintenance Agreement 2023 2026',
                'matter_no': 'AG2024/1344',
                'expiry_date': '14 May 2027',
                'approval_date': '14 May 2024',
                'company_name abn': '55008946969',
                'industry': 'Oil and gas industry',
                'storage_name': 'ae524605.pdf',
                'party_name': 'Applus Pty Ltd',
                'agmnt_type': 'Single-enterprise Agreement'
            },
            {
                'agmnt_id': 'AE524599',
                'agmnt_title': 'Danton Insulation & Sheetmetal Pty Ltd and CEPU Plumbing Division NSW Branch Mechanical Sheetmetal Enterprise Agreement 20232027',
                'matter_no': 'AG2024/1471',
                'expiry_date': '30 September 2027',
                'approval_date': '14 May 2024',
                'company_name abn': '95607448859',
                'industry': 'Building metal and civil construction industries',
                'storage_name': 'ae524599.pdf',
                'party_name': 'Danton Insulation & Sheetmetal Pty Ltd',
                'agmnt_type': 'Single-enterprise Agreement'
            },
            {
                'agmnt_id': 'AE524611',
                'agmnt_title': 'Timberlink Bell Bay Collective Agreement 2024',
                'matter_no': 'AG2024/1226',
                'expiry_date': '31 December 2026',
                'approval_date': '14 May 2024',
                'company_name abn': '12161713015',
                'industry': 'Timber and paper products industry',
                'storage_name': 'ae524611.pdf',
                'party_name': 'Timberlink Australia Pty Ltd',
                'agmnt_type': 'Single-enterprise Agreement'
            },
            {
                'agmnt_id': 'AE524614',
                'agmnt_title': 'Bidfood Lismore - Enterprise Agreement 2024',
                'matter_no': 'AG2024/1128',
                'expiry_date': '01 April 2027',
                'approval_date': '14 May 2024',
                'company_name abn': '',
                'industry': 'Food beverages and tobacco manufacturing industry',
                'storage_name': 'ae524614.pdf',
                'party_name': 'BFS Lismore Pty Ltd',
                'agmnt_type': 'Single-enterprise Agreement'
            },
            {
                'agmnt_id': 'AE524604',
                'agmnt_title': 'Protect Fire Systems Pty Ltd and CEPU - Plumbing Division Vic Fire Protection Enterprise Agreement 2024 - 2027',
                'matter_no': 'AG2024/1490',
                'expiry_date': '31 October 2027',
                'approval_date': '14 May 2024',
                'company_name abn': '98070495936',
                'industry': 'Plumbing industry',
                'storage_name': 'ae524604.pdf',
                'party_name': 'Protect Fire Systems Pty Ltd',
                'agmnt_type': 'Single-enterprise Agreement'
            },
            {
                'agmnt_id': 'AE524607',
                'agmnt_title': 'Hexion Brisbane Enterprise Agreement 2024',
                'matter_no': 'AG2024/1317',
                'expiry_date': '31 March 2027',
                'approval_date': '14 May 2024',
                'company_name abn': '',
                'industry': 'Manufacturing and associated industries',
                'storage_name': 'ae524607.pdf',
                'party_name': 'Lexi Bryant',
                'agmnt_type': 'Single-enterprise Agreement'
            },
            {
                'agmnt_id': 'AE524606',
                'agmnt_title': 'Taylors College Waterloo Campus Enterprise Agreement 2024',
                'matter_no': 'AG2024/1005',
                'expiry_date': '30 June 2025',
                'approval_date': '14 May 2024',
                'company_name abn': '88070919327',
                'industry': 'Educational services',
                'storage_name': 'ae524606.pdf',
                'party_name': 'Navitas Australia Pty Ltd',
                'agmnt_type': 'Single-enterprise Agreement'
            },
            {
                'agmnt_id': 'AE524526',
                'agmnt_title': 'Keppel Prince Enterprise Agreement 2024 for Workshops',
                'matter_no': 'AG2024/1366',
                'expiry_date': '30 September 2026',
                'approval_date': '14 May 2024',
                'company_name abn': '62004727619',
                'industry': 'Manufacturing and associated industries',
                'storage_name': 'ae524526.pdf',
                'party_name': 'Keppel Prince Engineering',
                'agmnt_type': 'Single-enterprise Agreement'
            },
            {
                'agmnt_id': 'AE524615',
                'agmnt_title': 'Bidfood Kalgoorlie - Enterprise Agreement 2024',
                'matter_no': 'AG2024/1305',
                'expiry_date': '01 March 2027',
                'approval_date': '14 May 2024',
                'company_name abn': '73092472118',
                'industry': 'Storage services',
                'storage_name': 'ae524615.pdf',
                'party_name': 'Goldline Distributors Pty Ltd',
                'agmnt_type': 'Single-enterprise Agreement'
            },
            {
                'agmnt_id': 'AE524594',
                'agmnt_title': 'Innovative Fire Services Pty Ltd & CEPU NSWNFIA Sprinkler Fitting Fire Protection Union Enterprise Agreement NSW & ACT 20242028',
                'matter_no': 'AG2024/1465',
                'expiry_date': '29 February 2028',
                'approval_date': '14 May 2024',
                'company_name abn': '49149191024',
                'industry': 'Plumbing industry',
                'storage_name': 'ae524594.pdf',
                'party_name': 'Innovative Fire Services Pty Ltd',
                'agmnt_type': 'Single-enterprise Agreement'
            },
            {
                'agmnt_id': 'AE524613',
                'agmnt_title': 'Boschetti Industries Pty Ltd Single Enterprise Agreement Trades 2023',
                'matter_no': 'AG2024/1245',
                'expiry_date': '30 November 2026',
                'approval_date': '14 May 2024',
                'company_name abn': '86163638846',
                'industry': 'Electrical contracting industry',
                'storage_name': 'ae524613.pdf',
                'party_name': 'Boschetti Industries Pty Ltd',
                'agmnt_type': 'Single-enterprise Agreement'
            },
            {
                'agmnt_id': 'AE524600',
                'agmnt_title': 'Cooke & Dowset Pty Ltd and CEPU - Plumbing Division Vic Plumbing Enterprise Agreement 2024 - 2027',
                'matter_no': 'AG2024/1473',
                'expiry_date': '31 October 2027',
                'approval_date': '14 May 2024',
                'company_name abn': '18129065694',
                'industry': 'Plumbing industry',
                'storage_name': 'ae524600.pdf',
                'party_name': 'Cooke & Dowsett Pty Ltd',
                'agmnt_type': 'Single-enterprise Agreement'
            },
            {
                'agmnt_id': 'AE524590',
                'agmnt_title': 'Cook Australia Enterprise Agreement 2024',
                'matter_no': 'AG2024/1179',
                'expiry_date': '13 May 2028',
                'approval_date': '13 May 2024',
                'company_name abn': '79005526723',
                'industry': 'Manufacturing and associated industries',
                'storage_name': 'ae524590.pdf',
                'party_name': 'William A. Cook Australia Pty Ltd',
                'agmnt_type': 'Single-enterprise Agreement'
            },
            {
                'agmnt_id': 'AE524589',
                'agmnt_title': 'Snow Brand Australia Pty Ltd Infant Formula Division and United Workers Union Enterprise Agreement 2023',
                'matter_no': 'AG2024/1394',
                'expiry_date': '30 June 2026',
                'approval_date': '13 May 2024',
                'company_name abn': '82057664034',
                'industry': 'Food beverages and tobacco manufacturing industry',
                'storage_name': 'ae524589.pdf',
                'party_name': 'Snow Brand Australia Pty Ltd',
                'agmnt_type': 'Single-enterprise Agreement'
            },
            {
                'agmnt_id': 'AE524591',
                'agmnt_title': 'Iplex Pipelines Australia Pty Ltd Enterprise Agreement 2023 Strathpine',
                'matter_no': 'AG2024/841',
                'expiry_date': '14 November 2026',
                'approval_date': '13 May 2024',
                'company_name abn': '',
                'industry': 'Manufacturing and associated industries',
                'storage_name': 'ae524591.pdf',
                'party_name': 'Kailem Perkins',
                'agmnt_type': 'Single-enterprise Agreement'
            },
            {
                'agmnt_id': 'AE524567',
                'agmnt_title': 'Application for approval of the Wood Offshore Brownfields Services Western Australia Greenfields Agreement 2024 - 2028',
                'matter_no': 'AG2024/1405',
                'expiry_date': '17 May 2028',
                'approval_date': '10 May 2024',
                'company_name abn': '79118514444',
                'industry': 'Oil and gas industry',
                'storage_name': 'ae524567.pdf',
                'party_name': 'Wood Australia Pty Ltd',
                'agmnt_type': 'Greenfields Agreement'
            },
            {
                'agmnt_id': 'AE524109',
                'agmnt_title': 'D&W Plumbing and Civil Contractors Pty Ltd and CEPU Plumbing Division - NSW Branch Plumbing Enterprise Agreement 2023-2027',
                'matter_no': 'AG2024/1003',
                'expiry_date': '30 September 2027',
                'approval_date': '10 May 2024',
                'company_name abn': '',
                'industry': 'Plumbing industry',
                'storage_name': 'ae524109-2.pdf',
                'party_name': 'D&W Plumbing And Civil Contractors Pty Ltd',
                'agmnt_type': 'Single-enterprise Agreement'
            }
        ]

        return data

    def create_table_data_headers(self, table_name):
        # create_table_data = {
        #     "description": "A to-do list of places to visit",
        #     "fields": [
        #         {"name": "agmnt_id", "type": "singleLineText"},
        #         {"name": "agmnt_title", "type": "singleLineText"},
        #         {"name": "matter_no", "type": "singleLineText"},
        #         {"name": "expiry_date", "type": "singleLineText"},
        #         {"name": "approval_date", "type": "singleLineText"},
        #         {"name": "company_name abn", "type": "singleLineText"},
        #         {"name": "industry", "type": "singleLineText"},
        #         {"name": "storage_name", "type": "singleLineText"},
        #         {"name": "party_name", "type": "singleLineText"},
        #         {"name": "agmnt_type", "type": "singleLineText"},
        #         {
        #             "name": "agmnt_id_link",
        #             "type": "formula",
        #             "options": {
        #                 "formula": "IF(agmnt_id, 'https://www.google.com/' & agmnt_id)"
        #             }
        #         }
        #     ],
        #     "name": "FWC Records"
        # }
        #
        # return create_table_data
        # Extract unique keys from self.records
        unique_keys = set()
        for record in self.records:
            unique_keys.update(record.keys())

        # Generate the fields list for the Airtable table
        fields = []
        for key in unique_keys:
            field_type = "singleLineText"  # Default type
            if "date" in key.lower():
                field_type = "date"  # Use date type for date fields
            # elif key == "Program Id Link":
            #     field_type = "url"  # Use url type for the link field
            fields.append({"name": key, "type": field_type})

        # Add the special formula field for Program Id Link
        # fields.append({
        #     "name": "Program Id Link",
        #     "type": "formula",
        #     "options": {
        #         "formula": "IF({Program ID}, 'https://www.google.com/' & {Program ID})"
        #     }
        # })

        create_table_data = {
            "description": "All records from the University",
            "fields": fields,
            # "name": "Uni records"
            "name": table_name
        }

        return create_table_data

    def read_input_data_from_json(self):
        file_path = glob.glob('input/*.json')[0]
        # Read and parse the JSON file
        with open(file_path, 'r') as file:
            data = json.load(file)

        # Convert all values to strings and add the pre-computed URL to each record
        for record in data:
            for key in record:
                record[key] = str(record[key])  # Convert value to string

            # Add the pre-computed URL to each record
            if 'Program ID' in record:
                record['Program Id Link'] = f"https://www.google.com/{record['Program ID']}"

        return data

    def get_previous_records_airtable(self,api, table_name):
        table = api.table('appcLQ4N9gSKf98ly', table_name)
        all_records = table.all()
        previous_program_ids = [record.get('fields', [{}]).get('Program ID', '') for record in all_records]

        return previous_program_ids

    def insert_records_airtable(self,table_name, previous_program_ids):
        insert_records_url = f'https://api.airtable.com/v0/appcLQ4N9gSKf98ly/{table_name}/'

        # check the current records already exist on airtable or not
        insert_records_ids = [row for row in self.records if row.get('Program ID') not in previous_program_ids]

        # limit of upload records are 10 so make batches of 10 records per batch
        batches = [insert_records_ids[i:i + 10] for i in range(0, len(insert_records_ids), 10)]
        for batch in batches:
            insert_records_data = {"records": [{"fields": record} for record in batch]}
            insert_records_req = requests.request(method='POST', url=insert_records_url, headers=self.headers,
                                                  data=json.dumps(insert_records_data))

            if insert_records_req.status_code == 200:
                print(f"{len(insert_records_data.get('records'))} :Records inserted successfully")
            else:
                print(f"Error: {insert_records_req.content}")

        return