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
    name = 'freida_airtable'
    base_url = 'www.airtable.com'
    start_urls = ['https://www.airtable.com']
    current_dt = datetime.now().strftime('%d%m%Y%H%M')

    custom_settings = {
        'CONCURRENT_REQUESTS': 4,
        'RETRY_TIMES': 5,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408],
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.api_token = 'pat3nmkWdDAV006vL.a5fe37f3419663e5351f78ca9d88938df03ce3c52c8e1c5cc4819e9b58697587'
        self.workspace_id = 'wspkHKNrPBF3B6V3N'
        self.logs_filepath = f'logs/logs {self.current_dt}.txt'

        # Table Program List
        self.table_program_list = 'Program List'
        self.table_program_list_records = self.read_csv_and_return_json(glob.glob('input/Results.csv')[0])
        self.table_program_list_headers = ['Program ID', 'Program Name', 'Specialty', 'Program City, State', 'Type of Program', 'Number of 1st Yr Positions', 'ERAS Participation', 'NRMP match', 'Program URL', 'Link to Overview', 'Link to ProgramWorkSchedule', 'Link to FeaturesBenefits']

        # Table Overview
        self.table_overview = 'Overview'
        # self.table_overview_records = []
        self.table_overview_records = self.read_csv_and_return_json(glob.glob('input/overview.csv')[0])

        # Table ProgramWorkSchedule
        self.table_programworkschedule = 'ProgramWorkSchedule'
        self.table_ProgramWorkSchedule_records = []

        # Table FeaturesBenefits
        self.table_featuresbenefits = 'FeaturesBenefits'
        self.table_featuresbenefits_records = []

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

        """program_list Table Functionalities"""

        create_table_url = f'https://api.airtable.com/v0/meta/bases/appcLQ4N9gSKf98ly/tables'

        # Create program_list Table
        create_table_req = requests.request(method='POST', url=create_table_url, headers=self.headers,
                                            data=json.dumps(self.create_table_data_headers(table_name=self.table_program_list, records=self.table_program_list_records, headers=self.table_program_list_headers)))
        table_program_list_previous_records = []
        if create_table_req.status_code == 200:
            print("Table created successfully")
        else:
            print(f"Error: {create_table_req.content}")
            table_program_list_previous_records = self.get_previous_records_airtable(api, table_name=self.table_program_list)

        # Step 2: Insert records into the table
        self.insert_records_airtable(current_records=self.table_program_list_records, table_name=self.table_program_list, previous_program_ids=table_program_list_previous_records)

        a=1
        """Overview Table Functionalities"""

        # # Overview program_list Table
        # create_table_req = requests.request(method='POST', url=create_table_url, headers=self.headers,
        #                                     data=json.dumps(self.create_table_data_headers(table_name=self.table_overview,
        #                                                                                    records=self.table_overview_records)))
        # table_overview_previous_records_ids = []
        # if create_table_req.status_code == 200:
        #     print("Table created successfully")
        # else:
        #     print(f"Error: {create_table_req.content}")
        #     table_overview_previous_records_ids = self.get_previous_records_airtable(api, table_name=self.table_overview)
        #
        # # Step 2: Insert records into the table
        # self.insert_records_airtable(current_records=self.table_overview_records, table_name=self.table_overview, previous_program_ids=table_overview_previous_records_ids)

        a=1

    def get_user_cred(self):
        credentials = {}
        with open('input/user_credentials.txt', mode='r', encoding='utf-8') as txt_file:
            for line in txt_file:
                key, value = line.strip().split('==')
                credentials[key.strip()] = value.strip()
        return credentials

    def create_table_data_headers(self, table_name, records, headers):
        # unique_keys = set()
        # for record in records:
        #     unique_keys.update(record.keys())
        #
        # # Generate the fields list for the Airtable table
        # fields = []
        # for key in unique_keys:
        #     field_type = "singleLineText"  # Default type
        #     fields.append({"name": key, "type": field_type})
        #
        # create_table_data = {
        #     "description": "All records from the University",
        #     "fields": headers,
        #     "name": table_name
        # }
        #
        # return create_table_data
        # Define a dictionary to map header names to their types and properties
        field_definitions = {
            # "Program ID": {"type": "singleLineText", "options": {"isUnique": True}},
            "Program ID": {"type": "number", "options": {"precision": 0}},
            "Program Name": {"type": "singleLineText"},
            # "Specialty": {"type": "singleSelect"},
            "Specialty": {
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "General"}  # Removed color option
                    ]
                }
            },
            "Program City, State": {"type": "singleLineText"},
            "Type of Program": {"type": "singleLineText"},
            "Number of 1st Yr Positions": {"type": "singleLineText"},
            "ERAS Participation": {"type": "singleLineText"},
            "NRMP match": {"type": "singleLineText"},
            "Program URL": {"type": "url"},
            "Link to Overview": {"type": "url"},
            "Link to ProgramWorkSchedule": {"type": "url"},
            "Link to FeaturesBenefits": {"type": "url"}
        }

        # Create the fields list based on the headers and their definitions
        fields = []
        for header in headers:
            if header in field_definitions:
                field = {"name": header, **field_definitions[header]}
            else:
                # Default to singleLineText if the header is not explicitly defined
                field = {"name": header, "type": "singleLineText"}
            fields.append(field)

        create_table_data = {
            "description": "All records from the University",
            "fields": fields,
            "name": table_name
        }

        return create_table_data

    def get_previous_records_airtable(self, api, table_name):
        table = api.table('appcLQ4N9gSKf98ly', table_name)
        all_records = table.all()
        previous_program_ids = [record.get('fields', [{}]).get('Program ID', '') for record in all_records]

        return previous_program_ids

    def insert_records_airtable(self, table_name, previous_program_ids, current_records):
        insert_records_url = f'https://api.airtable.com/v0/appcLQ4N9gSKf98ly/{table_name}/'

        # check the current records already exist on airtable or not
        insert_records_ids = [row for row in current_records if row.get('Program ID') not in previous_program_ids]

        if insert_records_ids is None:
            return

        # Convert boolean values to tick/cross signs
        for record in insert_records_ids:
            for key, value in record.items():
                if key == 'Program ID':
                    record[key] = int(value)
                if (key == 'ERAS Participation' and value.lower() == 'true') or (key == 'NRMP match' and value):
                    record[key] = '✓'
                elif key == 'ERAS Participation' and value.lower() == 'false':
                    record[key] = ''
                # elif 'type of program' in key.lower() and value == '':
                elif 'type of program' in key.lower() and value == '' or 'number of 1st yr positions' in key.lower() and value == '':
                    record[key] = 'N/A'

        # limit of upload records are 10 so make batches of 10 records per batch
        batches = [insert_records_ids[i:i + 10] for i in range(0, len(insert_records_ids), 10)]
        print('Total Records Uploading :', len(insert_records_ids))

        for batch in batches:
            insert_records_data = {"records": [{"fields": record} for record in batch]}
            insert_records_req = requests.request(method='POST', url=insert_records_url, headers=self.headers,
                                                  data=json.dumps(insert_records_data))
            b'{"error":{"type":"UNKNOWN_FIELD_NAME","message":"Unknown field name: \\"Link to Program Work Schedule\\""}}'
            if insert_records_req.status_code == 200:
                print(f"{len(insert_records_data.get('records'))} :Records inserted successfully")
            else:
                print(f"Error: {insert_records_req.content}")

        return None

    def read_csv_and_return_json(self, file_path):
        """
        Reads a CSV file and returns its contents as a JSON object.

        :param file_path: Path to the CSV file.
        :return: JSON object containing the CSV data.
        """

        data = []
        with open(file_path, mode='r', encoding='utf-8-sig') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                # Ensure all values are strings
                row = {key: str(value) for key, value in row.items()}
                data.append(row)
        return data

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
