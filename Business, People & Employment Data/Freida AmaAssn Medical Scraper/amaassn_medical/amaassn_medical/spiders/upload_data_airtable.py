import glob
import json
import requests
from time import sleep
from pyairtable import Api


# base_headers_list = ['Program ID']
base_headers_list = ['base id']
table_program_list = 'Program List'
table_program_list_columns = ['Program ID', 'Program Name', 'Specialty', 'Program City, State',
                              'Type of Program', 'Number of 1st Yr Positions', 'ERAS Participation', 'NRMP match',
                              'Program URL', 'Link to Overview', 'Link to ProgramWorkSchedule', 'Link to FeaturesBenefits']

table_overview = 'Overview'
table_overview_columns = ['Program ID', 'Description', 'University Affiliation', 'Primary Teaching Site',
                          'Accredited Training Length (years)', 'Required Length (years)', 'Accepting Apps 2024-2025',
                          'Accepting Apps 2025-2026', 'Program Start Dates', 'ERAS Participation',
                          'Government Affiliation', 'Web Address', 'Video Availability', 'Program Director',
                          'Director Contact Information', 'Director Tel.',
                          'Director Email', 'Contact Person', 'Contact Person Information', 'Contact Tel.',
                          'Contact Email', 'Last Updated', 'Survey Received', 'Location', 'Sponsor',
                          'Participant Institution 1',
                          'Participant Institution 2', 'Participant Institution 3', 'Participant Institution 4',
                          'Participant Institution 1 URL',
                          'Participant Institution 2 URL', 'Participant Institution 3 URL',
                          'Participant Institution 4 URL', 'Link to Program List']

table_programworkschedule = 'ProgramWorkSchedule'
table_programworkschedule_columns = ['Program ID', 'Year 1 Positions', 'Year 2 Positions', 'Year 3 Positions',
                                     'Year 4 Positions', 'Year 5 Positions', 'Year 6 Positions',
                                     'Requires Previous GME',
                                     'Offers Preliminary Positions', 'Participates in NRMP Main Match',
                                     'Main Match Codes', 'Participates in NRMP Advanced or Fellowship Match',
                                     'Advanced Match Codes',
                                     'Latest Application Date 2024-2025', 'Interview Period START 2024-2025',
                                     'Interview Period STOP 2024-2025', 'Earliest Application Date 2025-2026',
                                     'Latest Application Date 2025-2026', 'Interview Period START 2025-2026',
                                     'Interview Period STOP 2025-2026', 'Remote Interview Option',
                                     'Interviews Last Year',
                                     'Interview to Position Ratio', 'Participates in SF Match',
                                     'Participates in Other Matching Program',
                                     'Required Letters of Recommendation', 'Osteopathic Recognition', 'Step 1 Required',
                                     'Step 1 Minimum Score', 'Step 1 Pass Required', 'Step 2 Required',
                                     'Step 2 Pass Required',
                                     'Level 1 Required (DO)', 'Minimum Level 1 Score (DO)',
                                     'Level 1 Pass Required (DO)',
                                     'Level 2 Required (DO)', 'Level 2 Pass Required (DO)',
                                     'PGY1 Med School Grad Recency',
                                     'PGY1 Experience Requirement During Gap', 'J-1 Visa Sponsorship',
                                     'H-1B Visa', 'F-1 Visa (OPT)', 'Faculty Full Time MD', 'Faculty Part Time MD',
                                     'Faculty Full Time Non-MD', 'Faculty Part Time Non-MD', 'Total MD Faculty',
                                     'Total  Non-MD Faculty',
                                     '% FT Female Faculty', 'Ratio of FT Paid Faculty to Positions',
                                     'Avg Hours per Week (1st Year)',
                                     'Max Consecutive Hours (1st Year)', 'Avg Off Duty Periods per Week (1st Year)',
                                     'Moonlighting Allowed', 'Night Float System', 'USMD Percentage', 'IMG Percentage',
                                     'DO Percentage', 'Female Residents Percentage', 'Male Residents Percentage',
                                     'Call Schedule Year 1', 'Call Schedule Year 2', 'Call Schedule Year 3',
                                     'Call Schedule Year 4',
                                     'Call Schedule Year 5', 'Call Schedule Year 6', 'Beeper or Home Call Year 1',
                                     'Beeper or Home Call Year 2',
                                     'Beeper or Home Call Year 3', 'Beeper or Home Call Year 4',
                                     'Beeper or Home Call Year 5', 'Link to Program List']

table_featuresbenefits = 'FeaturesBenefits'
table_featuresbenefits_columns = ['Program ID', 'Avg Structured Didactic Hours Per Week',
                                  'Training in Hospital Outpatient Clinics (1st Year)',
                                  'Training in Non-Hospital Community-Based Settings (1st Year)', 'Salary Year 1',
                                  'Vacation Days Year 1', 'Sick Days Year 1', 'Salary Year 2', 'Vacation Days Year 2',
                                  'Sick Days Year 2',
                                  'Salary Year 3', 'Vacation Days Year 3', 'Sick Days Year 3', 'Salary Year 4',
                                  'Vacation Days Year 4',
                                  'Sick Days Year 4', 'Salary Paid by Non-profit Institution',
                                  'Max Paid Family Medical Leave Days',
                                  'Max Unpaid Family Medical Leave Days', 'Leave Policies URL',
                                  'Part-time/Shared Schedule Positions',
                                  'On-site Child Care', 'Subsidized Child Care', 'Moving Allowance', 'Housing Stipend',
                                  'Free Parking',
                                  'On-call Meal Allowance', 'Technology Allowance', 'Placement Assistance',
                                  'Policy Prohibits Hiring Smokers',
                                  'Additional Training Opportunities', 'Primary Care Track', 'Rural Track',
                                  "Women's Health Track", 'Hospitalist Track',
                                  'Research Track', 'Academic or Clinician Educator Track', 'Other Track',
                                  'Patient Surveys',
                                  'Portfolio System', 'OSCE', 'Major Medical Insurance (Residents)',
                                  'Major Medical Insurance (Dependents)',
                                  'Major Medical Insurance (Domestic Partners)', 'Outpatient Mental Health Insurance',
                                  'Inpatient Mental Health Insurance', 'Group Life Insurance', 'Dental Insurance',
                                  'Disability Insurance', 'Disability Insurance for HIV',
                                  'Integrative Medicine Curriculum',
                                  'Health Systems Leadership Curriculum', 'Interprofessional Teamwork',
                                  'Medical Spanish Instruction',
                                  'Alternative Medicine Curriculum', 'Health Care Systems Economics Curriculum',
                                  'Debt Management Counseling',
                                  'USMLE Step 3 Academic Support', 'International Experience',
                                  'Resident/Fellow Retreats', 'Off-campus Electives',
                                  'Hospice/Home Care Experience', 'Advanced Degree Training', 'Research Rotation',
                                  'Aggregate Milestone Achievements',
                                  'Board Certification Pass Rates', 'Performance-based Assessment Scores',
                                  'Link to Program List']

# Global table IDs
table_overview_id = ''
table_program_work_id = ''
table_featuresbenefits_id = ''


def read_user_cred_from_input_file():
    """
    Reads a text file and returns its contents as a dictionary.
    :return: Dictionary containing the text file data.
    """
    file_path = ''.join(glob.glob('input/airtable_creds.txt'))
    data = {}
    with open(file_path, mode='r', encoding='utf-8-sig') as text_file:
        for line in text_file:
            key, value = line.strip().split('==', maxsplit=1)
            data[key.strip()] = value.strip()
    return data


def get_university_data(detail_div, data):
    pattern = rf'.*?{data}.*'
    return detail_div.css('.ng-star-inserted::text').re_first(pattern)


""" Upload Data At Airtable """


def upload_airtable_data(data):
    airtable_request_headers = {
        'Authorization': f'Bearer {data.api_token}',
        'Content-Type': 'application/json',
    }

    api = Api(data.api_token)

    # Get user info
    user_info = api.whoami()
    data.mandatory_logs.append(f" User information : {user_info}")

    # Bases Info
    bases = api.bases()
    bases_info = {base.name: base.id for base in bases if base.id == data.base_id}
    if not bases_info:
        bases_info = get_bases_info(api=api, airtable_headers=airtable_request_headers, table_name='Base',
                                    workspace_id=data.workspace_id, table_headers=base_headers_list, data=data)
    data.mandatory_logs.append(f"Base Information: {bases_info}")
    ########################################
    """tables records in the specific Base """
    tables_info = get_tables_info(bases_info=bases_info, airtable_headers=airtable_request_headers, data=data)

    # Use First Base:
    base_name, base_id = next(iter(bases_info.items()))
    create_table_url = f'https://api.airtable.com/v0/meta/bases/{base_id}/tables'

    ########################################
    """Overview Table Functionalities"""
    upload_data_into_airtable_table(api=api, base_id=base_id, create_table_url=create_table_url, request_headers=airtable_request_headers,
                                    table_name=table_overview, table_columns=table_overview_columns, data=data, current_records=data.table_overview_records)

    ########################################
    """ProgramWorkSchedule Table Functionalities"""
    upload_data_into_airtable_table(api=api, base_id=base_id, create_table_url=create_table_url, request_headers=airtable_request_headers,
                                    table_name=table_programworkschedule, table_columns=table_programworkschedule_columns, data=data, current_records=data.table_programworkschedule_records)

    ########################################
    """FeaturesBenefits Table Functionalities"""

    upload_data_into_airtable_table(api=api, base_id=base_id, create_table_url=create_table_url, request_headers=airtable_request_headers,
                                    table_name=table_featuresbenefits, table_columns=table_featuresbenefits_columns, data=data, current_records=data.table_featuresbenefits_records)

    # Update global table IDs
    global table_overview_id, table_program_work_id, table_featuresbenefits_id
    table_overview_id, table_program_work_id, table_featuresbenefits_id = get_tables_id(api, base_id)
    a=1

    ########################################
    """program_list Table Functionalities"""
    upload_data_into_airtable_table(api=api, base_id=base_id, create_table_url=create_table_url,
                                    request_headers=airtable_request_headers,
                                    table_name=table_program_list, table_columns=table_program_list_columns, data=data,
                                    current_records=data.table_program_list_records)

    print(f"All Data Uploaded Successfully")
    data.mandatory_logs.append(f"All Records Uploaded Successfully\n")

    program_table = api.table(base_id, table_program_list).all()

    # table row record and their id
    record_detail = {rec.get('fields').get('Program ID'): rec.get('id', '') for rec in program_table}


def upload_data_into_airtable_table(api, base_id, create_table_url, request_headers, table_name, table_columns, data, current_records):
    create_table_req = requests.request(method='POST', url=create_table_url, headers=request_headers,
                                        data=json.dumps(create_table_data_headers(table_name=table_name, headers=table_columns)))
    table_previous_records = []
    if create_table_req.status_code == 200:
        print(f"Table: {table_name} created successfully")
    elif 'DUPLICATE_TABLE_NAME' in str(create_table_req.content):
        print(f"Table :{table_name} Already exist")
        table_previous_records = get_previous_records_airtable(api, base_id, table_name=table_name, data=data)
    else:
        print(f"Error: {create_table_req.content}")
        data.error.append(
            f"Table :{table_name} Not created Successfully Error: {json.loads(create_table_req.content).get('error', {}).get('message', '')}")

    # modified_current_records = [{col: item.get(col)} for col in table_columns for item in current_records]
    modified_current_records = [dict((col, item.get(col)) for col in table_columns) for item in current_records]

    # Step 2: Insert records into the table
    insert_records_airtable(current_records=modified_current_records, table_name=table_name,
                            previous_program_ids=table_previous_records, base_id=base_id,
                            headers=request_headers, data=data)

    return


def create_table_data_headers(table_name, headers):
    field_definitions = {}

    if table_name == 'Program List':
        # Program list table headers
        field_definitions = {
            'Program ID': {'type': 'number', 'options': {'precision': 0}},
            'Program Name': {'type': 'singleLineText'},
            'Specialty': {'type': 'singleLineText'},
            'Program City, State': {'type': 'singleLineText'},
            'Type of Program': {'type': 'singleLineText'},
            'Number of 1st Yr Positions': {'type': 'singleLineText'},
            'ERAS Participation': {'type': 'checkbox', 'options': {'color': 'greenBright', 'icon': 'check'}},
            'NRMP match': {'type': 'checkbox', 'options': {'color': 'greenBright', 'icon': 'check'}},
            'Program URL': {'type': 'url'},
            'Link to Overview': {'type': 'multipleRecordLinks', 'options': {'linkedTableId': table_overview_id}},
            'Link to ProgramWorkSchedule': {'type': 'multipleRecordLinks', 'options': {'linkedTableId': table_program_work_id}},
            'Link to FeaturesBenefits': {'type': 'multipleRecordLinks', 'options': {'linkedTableId': table_featuresbenefits_id}},
        }

    elif table_name == 'Overview':
        # Table overview Headers
        field_definitions = {
            'Program ID': {'type': 'number', 'options': {'precision': 0}},
            'Description': {'type': 'singleLineText'},
            'University Affiliation': {'type': 'singleLineText'},
            'Primary Teaching Site': {'type': 'singleLineText'},
            'Accredited Training Length (years)': {'type': 'number', 'options': {'precision': 0}},
            'Required Length (years)': {'type': 'number', 'options': {'precision': 0}},
            'Accepting Apps 2024-2025': {'type': 'singleLineText'},
            'Accepting Apps 2025-2026': {'type': 'checkbox', 'options': {'color': 'greenBright', 'icon': 'check'}},
            'Program Start Dates': {'type': 'singleLineText'},
            'ERAS Participation': {'type': 'checkbox', 'options': {'color': 'greenBright', 'icon': 'check'}},
            'Government Affiliation': {'type': 'singleLineText'},
            'Web Address': {'type': 'url'},
            'Video Availability': {'type': 'singleLineText'},
            'Program Director': {'type': 'singleLineText'},
            'Director Contact Information': {'type': 'richText'},
            'Director Tel.': {'type': 'singleLineText'},
            'Director Email': {'type': 'singleLineText'},
            'Contact Person': {'type': 'singleLineText'},
            'Contact Person Information': {'type': 'singleLineText'},
            'Contact Tel.': {'type': 'singleLineText'},
            'Contact Email': {'type': 'singleLineText'},
            'Last Updated': {'type': 'date', 'options': {'dateFormat': {'format': 'M/D/YYYY', 'name': 'us'}}},
            'Survey Received': {'type': 'date', 'options': {'dateFormat': {'format': 'M/D/YYYY', 'name': 'us'}}},
            'Location': {'type': 'richText'},
            'Sponsor': {'type': 'singleLineText'},
            'Participant Institution 1': {'type': 'richText'},
            'Participant Institution 2': {'type': 'richText'},
            'Participant Institution 3': {'type': 'richText'},
            'Participant Institution 4': {'type': 'richText'},
            'Participant Institution 1 URL': {'type': 'url'},
            'Participant Institution 2 URL': {'type': 'url'},
            'Participant Institution 3 URL': {'type': 'url'},
            'Participant Institution 4 URL': {'type': 'url'},
            'Link to Program List': {'type': 'url'},
        }

    elif table_name == 'ProgramWorkSchedule':
        # Table ProgramWorkSchedule Headers
        field_definitions = {
            'Program ID': {'type': 'number', 'options': {'precision': 0}},
            'Year 1 Positions': {'type': 'number', 'options': {'precision': 0}},
            'Year 2 Positions': {'type': 'number', 'options': {'precision': 0}},
            'Year 3 Positions': {'type': 'number', 'options': {'precision': 0}},
            'Year 4 Positions': {'type': 'number', 'options': {'precision': 0}},
            'Year 5 Positions': {'type': 'number', 'options': {'precision': 0}},
            'Year 6 Positions': {'type': 'number', 'options': {'precision': 0}},
            'Requires Previous GME': {'type': 'singleLineText'},
            'Offers Preliminary Positions': {'type': 'checkbox', 'options': {'color': 'greenBright', 'icon': 'check'}},
            'Participates in NRMP Main Match': {'type': 'checkbox',
                                                'options': {'color': 'greenBright', 'icon': 'check'}},
            'Main Match Codes': {'type': 'singleLineText'},
            'Participates in NRMP Advanced or Fellowship Match': {'type': 'checkbox',
                                                                  'options': {'color': 'greenBright', 'icon': 'check'}},
            'Advanced Match Codes': {'type': 'singleLineText'},
            'Latest Application Date 2024-2025': {'type': 'date',
                                                  'options': {'dateFormat': {'format': 'M/D/YYYY', 'name': 'us'}}},
            'Interview Period START 2024-2025': {'type': 'date',
                                                 'options': {'dateFormat': {'format': 'M/D/YYYY', 'name': 'us'}}},
            'Interview Period STOP 2024-2025': {'type': 'date',
                                                'options': {'dateFormat': {'format': 'M/D/YYYY', 'name': 'us'}}},
            'Earliest Application Date 2025-2026': {'type': 'date',
                                                    'options': {'dateFormat': {'format': 'M/D/YYYY', 'name': 'us'}}},
            'Latest Application Date 2025-2026': {'type': 'date',
                                                  'options': {'dateFormat': {'format': 'M/D/YYYY', 'name': 'us'}}},
            'Interview Period START 2025-2026': {'type': 'date',
                                                 'options': {'dateFormat': {'format': 'M/D/YYYY', 'name': 'us'}}},
            'Interview Period STOP 2025-2026': {'type': 'date',
                                                'options': {'dateFormat': {'format': 'M/D/YYYY', 'name': 'us'}}},
            'Remote Interview Option': {'type': 'checkbox', 'options': {'color': 'greenBright', 'icon': 'check'}},
            'Interviews Last Year': {'type': 'number', 'options': {'precision': 0}},
            'Interview to Position Ratio': {'type': 'singleLineText'},
            'Participates in SF Match': {'type': 'checkbox', 'options': {'color': 'greenBright', 'icon': 'check'}},
            'Participates in Other Matching Program': {'type': 'checkbox',
                                                       'options': {'color': 'greenBright', 'icon': 'check'}},
            'Required Letters of Recommendation': {'type': 'number', 'options': {'precision': 0}},
            'Osteopathic Recognition': {'type': 'checkbox', 'options': {'color': 'greenBright', 'icon': 'check'}},
            'Step 1 Required': {'type': 'checkbox', 'options': {'color': 'greenBright', 'icon': 'check'}},
            'Step 1 Minimum Score': {'type': 'number', 'options': {'precision': 0}},
            'Step 1 Pass Required': {'type': 'checkbox', 'options': {'color': 'greenBright', 'icon': 'check'}},
            'Step 2 Required': {'type': 'singleLineText'},
            'Step 2 Pass Required': {'type': 'singleLineText'},
            'Level 1 Required (DO)': {'type': 'singleLineText'},
            'Minimum Level 1 Score (DO)': {'type': 'number', 'options': {'precision': 0}},
            'Level 1 Pass Required (DO)': {'type': 'checkbox', 'options': {'color': 'greenBright', 'icon': 'check'}},
            'Level 2 Required (DO)': {'type': 'singleLineText'},
            'Level 2 Pass Required (DO)': {'type': 'checkbox', 'options': {'color': 'greenBright', 'icon': 'check'}},
            'PGY1 Med School Grad Recency': {'type': 'number', 'options': {'precision': 0}},
            'PGY1 Experience Requirement During Gap': {'type': 'singleLineText'},
            'J-1 Visa Sponsorship': {'type': 'checkbox', 'options': {'color': 'greenBright', 'icon': 'check'}},
            'H-1B Visa': {'type': 'checkbox', 'options': {'color': 'greenBright', 'icon': 'check'}},
            'F-1 Visa (OPT)': {'type': 'singleLineText'},
            'Faculty Full Time MD': {'type': 'number', 'options': {'precision': 0}},
            'Faculty Part Time MD': {'type': 'number', 'options': {'precision': 0}},
            'Faculty Full Time Non-MD': {'type': 'number', 'options': {'precision': 0}},
            'Faculty Part Time Non-MD': {'type': 'number', 'options': {'precision': 0}},
            'Total MD Faculty': {'type': 'number', 'options': {'precision': 0}},
            'Total  Non-MD Faculty': {'type': 'number', 'options': {'precision': 0}},
            '% FT Female Faculty': {'type': 'singleLineText'},
            'Ratio of FT Paid Faculty to Positions': {'type': 'number', 'options': {'precision': 2}},
            'Avg Hours per Week (1st Year)': {'type': 'number', 'options': {'precision': 0}},
            'Max Consecutive Hours (1st Year)': {'type': 'number', 'options': {'precision': 0}},
            'Avg Off Duty Periods per Week (1st Year)': {'type': 'number', 'options': {'precision': 2}},
            'Moonlighting Allowed': {'type': 'checkbox', 'options': {'color': 'greenBright', 'icon': 'check'}},
            'Night Float System': {'type': 'checkbox', 'options': {'color': 'greenBright', 'icon': 'check'}},
            'USMD Percentage': {'type': 'singleLineText'},
            'IMG Percentage': {'type': 'singleLineText'},
            'DO Percentage': {'type': 'singleLineText'},
            'Female Residents Percentage': {'type': 'singleLineText'},
            'Male Residents Percentage': {'type': 'singleLineText'},
            'Call Schedule Year 1': {'type': 'singleLineText'},
            'Call Schedule Year 2': {'type': 'singleLineText'},
            'Call Schedule Year 3': {'type': 'singleLineText'},
            'Call Schedule Year 4': {'type': 'singleLineText'},
            'Call Schedule Year 5': {'type': 'singleLineText'},
            'Call Schedule Year 6': {'type': 'singleLineText'},
            'Beeper or Home Call Year 1': {'type': 'singleLineText'},
            'Beeper or Home Call Year 2': {'type': 'singleLineText'},
            'Beeper or Home Call Year 3': {'type': 'singleLineText'},
            'Beeper or Home Call Year 4': {'type': 'singleLineText'},
            'Beeper or Home Call Year 5': {'type': 'singleLineText'},
            'Link to Program List': {'type': 'singleLineText'},
        }

    elif table_name == 'FeaturesBenefits':
        field_definitions = {
            'Program ID': {'type': 'number', 'options': {'precision': 0}},
            'Avg Structured Didactic Hours Per Week': {'type': 'number', 'options': {'precision': 1}},
            'Training in Hospital Outpatient Clinics (1st Year)': {'type': 'number', 'options': {'precision': 0}},
            'Training in Non-Hospital Community-Based Settings (1st Year)': {'type': 'singleLineText'},
            'Salary Year 1': {'type': 'singleLineText'},
            'Vacation Days Year 1': {'type': 'number', 'options': {'precision': 0}},
            'Sick Days Year 1': {'type': 'number', 'options': {'precision': 0}},
            'Salary Year 2': {'type': 'singleLineText'},
            'Vacation Days Year 2': {'type': 'number', 'options': {'precision': 0}},
            'Sick Days Year 2': {'type': 'number', 'options': {'precision': 0}},
            'Salary Year 3': {'type': 'singleLineText'},
            'Vacation Days Year 3': {'type': 'number', 'options': {'precision': 0}},
            'Sick Days Year 3': {'type': 'number', 'options': {'precision': 0}},
            'Salary Year 4': {'type': 'singleLineText'},
            'Vacation Days Year 4': {'type': 'number', 'options': {'precision': 0}},
            'Sick Days Year 4': {'type': 'number', 'options': {'precision': 0}},
            'Salary Paid by Non-profit Institution': {'type': 'checkbox',
                                                      'options': {'color': 'greenBright', 'icon': 'check'}},
            'Max Paid Family Medical Leave Days': {'type': 'singleLineText'},
            'Max Unpaid Family Medical Leave Days': {'type': 'singleLineText'},
            'Leave Policies URL': {'type': 'url'},
            'Part-time/Shared Schedule Positions': {'type': 'singleLineText'},
            'On-site Child Care': {'type': 'singleLineText'},
            'Subsidized Child Care': {'type': 'singleLineText'},
            'Moving Allowance': {'type': 'checkbox', 'options': {'color': 'greenBright', 'icon': 'check'}},
            'Housing Stipend': {'type': 'checkbox', 'options': {'color': 'greenBright', 'icon': 'check'}},
            'Free Parking': {'type': 'singleLineText'},
            'On-call Meal Allowance': {'type': 'checkbox', 'options': {'color': 'greenBright', 'icon': 'check'}},
            'Technology Allowance': {'type': 'checkbox', 'options': {'color': 'greenBright', 'icon': 'check'}},
            'Placement Assistance': {'type': 'checkbox', 'options': {'color': 'greenBright', 'icon': 'check'}},
            'Policy Prohibits Hiring Smokers': {'type': 'singleLineText'},
            'Additional Training Opportunities': {'type': 'singleLineText'},
            'Primary Care Track': {'type': 'singleLineText'},
            'Rural Track': {'type': 'singleLineText'},
            "Women's Health Track": {'type': 'singleLineText'},
            'Hospitalist Track': {'type': 'singleLineText'},
            'Research Track': {'type': 'checkbox', 'options': {'color': 'greenBright', 'icon': 'check'}},
            'Academic or Clinician Educator Track': {'type': 'checkbox',
                                                     'options': {'color': 'greenBright', 'icon': 'check'}},
            'Other Track': {'type': 'singleLineText'},
            'Patient Surveys': {'type': 'checkbox', 'options': {'color': 'greenBright', 'icon': 'check'}},
            'Portfolio System': {'type': 'checkbox', 'options': {'color': 'greenBright', 'icon': 'check'}},
            'OSCE': {'type': 'checkbox', 'options': {'color': 'greenBright', 'icon': 'check'}},
            'Major Medical Insurance (Residents)': {'type': 'singleLineText'},
            'Major Medical Insurance (Dependents)': {'type': 'singleLineText'},
            'Major Medical Insurance (Domestic Partners)': {'type': 'singleLineText'},
            'Outpatient Mental Health Insurance': {'type': 'singleLineText'},
            'Inpatient Mental Health Insurance': {'type': 'singleLineText'},
            'Group Life Insurance': {'type': 'singleLineText'},
            'Dental Insurance': {'type': 'singleLineText'},
            'Disability Insurance': {'type': 'singleLineText'},
            'Disability Insurance for HIV': {'type': 'singleLineText'},
            'Integrative Medicine Curriculum': {'type': 'checkbox',
                                                'options': {'color': 'greenBright', 'icon': 'check'}},
            'Health Systems Leadership Curriculum': {'type': 'checkbox',
                                                     'options': {'color': 'greenBright', 'icon': 'check'}},
            'Interprofessional Teamwork': {'type': 'checkbox', 'options': {'color': 'greenBright', 'icon': 'check'}},
            'Medical Spanish Instruction': {'type': 'singleLineText'},
            'Alternative Medicine Curriculum': {'type': 'checkbox',
                                                'options': {'color': 'greenBright', 'icon': 'check'}},
            'Health Care Systems Economics Curriculum': {'type': 'checkbox',
                                                         'options': {'color': 'greenBright', 'icon': 'check'}},
            'Debt Management Counseling': {'type': 'checkbox', 'options': {'color': 'greenBright', 'icon': 'check'}},
            'USMLE Step 3 Academic Support': {'type': 'singleLineText'},
            'International Experience': {'type': 'checkbox', 'options': {'color': 'greenBright', 'icon': 'check'}},
            'Resident/Fellow Retreats': {'type': 'checkbox', 'options': {'color': 'greenBright', 'icon': 'check'}},
            'Off-campus Electives': {'type': 'checkbox', 'options': {'color': 'greenBright', 'icon': 'check'}},
            'Hospice/Home Care Experience': {'type': 'singleLineText'},
            'Advanced Degree Training': {'type': 'checkbox', 'options': {'color': 'greenBright', 'icon': 'check'}},
            'Research Rotation': {'type': 'singleLineText'},
            'Aggregate Milestone Achievements': {'type': 'checkbox',
                                                 'options': {'color': 'greenBright', 'icon': 'check'}},
            'Board Certification Pass Rates': {'type': 'checkbox',
                                               'options': {'color': 'greenBright', 'icon': 'check'}},
            'Performance-based Assessment Scores': {'type': 'checkbox',
                                                    'options': {'color': 'greenBright', 'icon': 'check'}},
            'Link to Program List': {'type': 'singleLineText'},
        }

    # Create the fields list based on the headers and their definitions
    fields = []
    for header in headers:
        if header in field_definitions:
            field = {'name': header, **field_definitions[header]}
        else:
            field = {'name': header, 'type': 'singleLineText'}
        fields.append(field)

    create_table_data = {
        'description': 'All records from the University',
        'fields': fields,
        'name': table_name
    }

    return create_table_data


def get_previous_records_airtable(api, base_id, table_name, data):
    print('Request for previous Records in the table : ', table_name)
    data.mandatory_logs.append(f"")
    table = api.table(base_id, table_name)
    all_records = table.all()
    previous_program_ids = [record.get('fields', {}).get('Program ID', 0) for record in all_records]
    previous_program_ids = [str(pid) for pid in previous_program_ids]
    data.mandatory_logs.append(f"{len(previous_program_ids)} Previous records found for the table : {table_name} ")

    return previous_program_ids


def insert_records_airtable(table_name, previous_program_ids, current_records, base_id, headers, data):
    insert_records_url = f'https://api.airtable.com/v0/{base_id}/{table_name}/'

    # check the current records already exist on airtable or not
    insert_records_ids = [row for row in current_records if
                          row.get('Program ID', '').lstrip('0') not in previous_program_ids]

    if insert_records_ids is None:
        print(f"No records upload for table {table_name}")
        return

    for record in insert_records_ids:
        for key, value in record.items():
            if key == 'Program ID':
                record[key] = int(value)
            elif key == 'ERAS Participation':
                record[key] = True if str(value) == 'True' else False
            elif key == 'NRMP match':
                record[key] = True if str(value) == 'True' else False
            elif 'type of program' in key.lower() and value == '' or 'number of 1st yr positions' in key.lower() and value == '':
                record[key] = 'N/A'

    # limit of upload records are 10 so make batches of 10 records per batch
    batches = [insert_records_ids[i:i + 10] for i in range(0, len(insert_records_ids), 10)]
    data.mandatory_logs.append(f"Inserting {len(insert_records_ids)} records in the Table: {table_name}")

    for batch in batches:
        insert_records_data = {"records": [{"fields": record} for record in batch]}

        insert_records_req = requests.request(method='POST', url=insert_records_url, headers=headers, data=json.dumps(insert_records_data))

        if insert_records_req.status_code == 200:
            print(f"{len(insert_records_data.get('records'))} :Records inserted successfully in Table :{table_name}")

        elif insert_records_req.status_code == 429:
            print(f" Request limit exceed please wait 30 seconds for next request")
            sleep(32)
            requests.request(method='POST', url=insert_records_url, headers=headers,
                             data=json.dumps(insert_records_data))
        else:
            print(f"Table Name : {table_name}")
            print(f"Error: {insert_records_req.content}")

            """ If error arises then the batch uploading is canceled now upload the individual records 
                Retry each record individually to identify and skip invalid records """
            for record in batch:
                insert_record_data = {"records": [{"fields": record}]}
                insert_record_req = requests.request(method='POST', url=insert_records_url, headers=headers,
                                                     data=json.dumps(insert_record_data))

                if insert_record_req.status_code == 200:
                    print(f"one Record inserted successfully In Table :{table_name}")
                elif insert_record_req.status_code == 429:
                    print(f"Request limit exceeded, please wait 30 seconds for the next request")
                    sleep(32)
                    requests.request(method='POST', url=insert_records_url, headers=headers,
                                     data=json.dumps(insert_record_data))
                else:
                    print(f"Error inserting individual record: {insert_record_req.content}")
                    data.error.append(f"record Not upload Program Id :{record.get('Program ID', 0)} in table :{table_name}")

    return None


def base_headers(table_name, workspace_id, headers):
    fields = [{'name': header, 'type': 'singleLineText'} for header in headers]

    data = {
        'name': 'Base Freida Records',
        "tables": [
            {
                "description": "Main Programs of Universities",
                "fields": fields,
                'name': table_name
            }
        ],
        "workspaceId": workspace_id
    }

    return data


def get_bases_info(api, airtable_headers, table_name, workspace_id, table_headers, data):
    bases_info = {}
    bases = api.bases()
    for base in bases:
        bases_info[base.name] = base.id

    # if NO base Found then create new one
    if not bases_info:
        data.error.append(f"No Base exist request to create new one Base")
        url = 'https://api.airtable.com/v0/meta/bases'
        create_base = requests.request(method='POST', url=url, headers=airtable_headers,
                                       data=json.dumps(base_headers(table_name=table_name, workspace_id=workspace_id,
                                                                    headers=table_headers)))

        if create_base.status_code == 200:
            req = requests.request(method='Get', url='https://api.airtable.com/v0/meta/bases', headers=airtable_headers)
            bases = req.json().get('bases', [])
            for base in bases:
                bases_info[base.get('name')] = base.get('id')
            print(f"New BAse create in the workspace is : {bases_info}")

    return bases_info


def get_tables_info(bases_info, airtable_headers, data):
    if bases_info:
        # for base_name, base_id in bases_info.items():
        base_name, base_id = next(iter(bases_info.items()))
        print(f"Request made for getting information already exists tables on the Base: {base_name} ")

        url = f'https://api.airtable.com/v0/meta/bases/{base_id}/tables'
        base_detail = requests.get(url, headers=airtable_headers)
        tables_info = {}
        if base_detail.status_code == 200:
            for table in base_detail.json().get('tables', [{}]):
                tables_info[table.get('name', '')] = table.get('id', '')

        print(f" tables on the Base: {base_name} are : {tables_info} ")

        data.mandatory_logs.append(f"Base Name: {base_name} Has these Tables: {tables_info}")

        return tables_info


def get_tables_id(api, base_id):
    tables = api.base(base_id=base_id).tables()

    table_overview_id = ''
    table_program_work_id = ''
    table_featuresbenefits_id = ''

    for table in tables:
        if table.name == table_overview:
            table_overview_id = table.id
        elif table.name == table_programworkschedule:
            table_program_work_id = table.id
        elif table.name == table_featuresbenefits:
            table_featuresbenefits_id = table.id

    return table_overview_id, table_program_work_id, table_featuresbenefits_id

