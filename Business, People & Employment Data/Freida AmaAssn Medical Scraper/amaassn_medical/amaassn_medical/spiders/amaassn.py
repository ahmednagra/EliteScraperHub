import json
import os
import re
from datetime import datetime

from scrapy import Spider, Request
from collections import OrderedDict

# import function file
from .upload_data_airtable import read_user_cred_from_input_file, get_university_data, upload_airtable_data


class AmaassnSpider(Spider):
    name = "amaassn"
    start_urls = ["https://freida.ama-assn.org/search/list?spec=42646,43516,43451,43431&page=1"]
    current_dt = datetime.now().strftime('%d%m%Y%H%M')

    custom_settings = {
        'CONCURRENT_REQUESTS': 5,
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 0.2,
        'AUTOTHROTTLE_MAX_DELAY': 3,

        'RETRY_TIMES': 5,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408, 429],
    }

    def __init__(self, *args, **kwargs):
        super(AmaassnSpider, self).__init__(*args, **kwargs)
        self.included = {}

        self.logs_filepath = f'logs/logs {self.current_dt}.txt'
        self.error = []
        self.mandatory_logs = [f'Spider "{self.name}" Started at "{self.current_dt}"\n']

        self.programs_counter = 0
        self.overview_counter = 0
        self.programworkschedule_counter = 0
        self.featuresbenefits_counter = 0

        """ Variables Declared for the Airtable Data upload in various tables"""
        self.airtable_creds = read_user_cred_from_input_file()
        self.api_token = self.airtable_creds.get('api_token', '')
        self.workspace_id = self.airtable_creds.get('workspace_id', '')
        self.base_id = self.airtable_creds.get('base_id', '')

        # Airtable's Records
        self.table_program_list_records = []
        self.table_overview_records = []
        self.table_programworkschedule_records = []
        self.table_featuresbenefits_records = []

    def start_requests(self):
        yield Request(url=self.start_urls[0])

    def parse(self, response, **kwargs):
        for detail_div in response.css('#search-result-list .search-list__result'):
            banner_check = detail_div.css('div .search-list__result__banner')

            if banner_check:
                continue

            program_url = detail_div.css('.search-result-card__title::attr(href)').get('')
            program_id = detail_div.css('.search-result-card__footer div:contains(ID) ::text').re_first(
                r'\d+') or ''

            item = OrderedDict()
            item['Program ID'] = program_id
            item['Program Name'] = detail_div.css('h4::text').get('')
            item['Specialty'] = detail_div.css('.search-result-card__specialty-name::text').get('')
            item['Program City, State'] = detail_div.css('.search-result-card__footer div ::text').get('')
            item['Type of Program'] = get_university_data(detail_div, '-based')
            item['Number of 1st Yr Positions'] = get_university_data(detail_div, 'position')
            item['ERAS Participation'] = True if get_university_data(detail_div, 'ERAS') else False
            item['NRMP match'] = True if get_university_data(detail_div, 'NRMP') else False
            item['Program URL'] = f"https://freida.ama-assn.org{program_url}" if program_url else ''

            item['Link to Overview'] = ''
            item['Link to ProgramWorkSchedule'] = ''
            item['Link to FeaturesBenefits'] = ''

            self.table_program_list_records.append(item)
            self.programs_counter += 1
            print(f"{self.programs_counter} Programs scraped.")

            id_for_url = detail_div.css('.search-result-card__title::attr(href)').get('')
            url = f'https://freida-admin.ama-assn.org/router/translate-path?path={id_for_url}&_format=json'

            yield Request(url=url, callback=self.get_uuid, meta={'program_name': item['Program Name'], 'program_id': item['Program ID']})

        current_page = response.css('.ama-pagination__button--primary--active::text').get('')

        if current_page:
            next_page_url = f'https://freida.ama-assn.org/search/list?spec=42646,43516,43451,43431&page={int(current_page) + 1}'

            yield Request(url=next_page_url, callback=self.parse)

    def get_uuid(self, response):
        try:
            data_dict = response.json()
        except json.JSONDecodeError as e:
            self.error.append(
                f"Error Parsing json response from Program: {response.meta.get('program_name', '')} Error : {e}")
            return

        id_for_url = data_dict.get('entity', {}).get('uuid', '')
        url = f"https://freida-admin.ama-assn.org/api/node/program/{id_for_url}?include=field_image.field_media_image,field_specialty,field_survey,field_survey.field_program_director,field_survey.field_program_contact,field_survey.field_primary_teaching_site,field_institution,field_participant_institution,field_sponsor_institution,field_video"
        yield Request(url=url, callback=self.parse_details, meta=response.meta)

    def parse_details(self, response):
        try:
            data_dict = response.json()
        except json.JSONDecodeError as e:
            self.error.append(
                f"Error Parsing json response at detail Page from Program: {response.meta.get('program_name', '')} error : {e}")
            return

        included = data_dict.get('included', [])
        data = data_dict.get('data', {})

        # Program OverView Detail
        self.get_overview_detail(response, included, data)

        # Program & Work Schedule Detail
        self.get_program_schedule_detail(response, included)

        # Features & Benefits
        self.get_features_and_benefits(response, included)

    def get_overview_detail(self, response, included, data):
        try:
            program_id = self.get_value_from_included(included[1], 'field_program_id')
            if not program_id:
                return

            last_updated = self.extract_date(self.get_value_from_included(included[1], 'changed'))
            survey_received = self.extract_date(self.get_value_from_included(included[1], 'field_date_received'))
            item = OrderedDict()
            item['Program ID'] = program_id
            item['Description'] = self.get_value_from_included(included[1], 'field_program_best_described_as')
            item['University Affiliation'] = f"{included[2].get('attributes', {}).get('field_address', {}).get('locality', '')} University"
            item['Primary Teaching Site'] = self.get_value_from_included(included[4], 'title')
            item['Accredited Training Length (years)'] = self.get_value_from_data(data, 'field_accredited_length')
            item['Required Length (years)'] = self.get_value_from_data(data, 'field_required_length')
            item['Accepting Apps 2024-2025'] = self.convert_bool_to_yes_no(self.get_value_from_included(included[1], 'field_accepting_current_year'))
            item['Accepting Apps 2025-2026'] = self.get_value_from_included(included[1], 'field_accepting_next_year')
            item['Program Start Dates'] = self.get_program_start_included(included)
            item['ERAS Participation'] = self.get_value_from_included(included[1], 'field_participates_in_eras')
            item['Government Affiliation'] = self.check_government_affiliation(self.get_value_from_data(data, 'field_affiliated_us_gov'))
            item['Web Address'] = self.get_value_from_included(included[1], 'field_website')
            item['Video Availability'] = self.check_video_availability(included)
            item['Program Director'] = self.get_person_name_from_included(included[2])
            item['Director Contact Information'] = self.get_person_information_from_included(included[2])
            item['Director Tel.'] = self.get_value_from_included(included[2], 'field_phone')
            item['Director Email'] = self.get_value_from_included(included[2], 'field_email')
            item['Contact Person'] = self.get_person_name_from_included(included[3])
            item['Contact Person Information'] = self.get_person_information_from_included(included[3])
            item['Contact Tel.'] = self.get_value_from_included(included[3], 'field_phone')
            item['Contact Email'] = self.get_value_from_included(included[3], 'field_email')
            item['Last Updated'] = self.convert_date_to_american_format(last_updated) if last_updated else None
            item['Survey Received'] = self.convert_date_to_american_format(survey_received) if survey_received else None
            item['Location'] = self.get_location_from_included(included[2])
            item['Sponsor'] = self.get_value_from_included(included[4], 'title')
            item['Participant Institution 1'] = self.get_participant_institution_address_from_included(included, 5)
            item['Participant Institution 2'] = self.get_participant_institution_address_from_included(included, 6)
            item['Participant Institution 3'] = self.get_participant_institution_address_from_included(included, 7)
            item['Participant Institution 4'] = self.get_participant_institution_address_from_included(included, 8)
            item['Participant Institution 1 URL'] = self.get_participant_institution_url_from_included(included, 5)
            item['Participant Institution 2 URL'] = self.get_participant_institution_url_from_included(included, 6)
            item['Participant Institution 3 URL'] = self.get_participant_institution_url_from_included(included, 7)
            item['Participant Institution 4 URL'] = self.get_participant_institution_url_from_included(included, 8)
            # item['Link to Program List'] = response.meta.get('program_id', '')
            item['Link to Program List'] = ''

            self.overview_counter += 1
            print(f"Overview Counter : {self.overview_counter}")
            self.table_overview_records.append(item)
        except Exception as e:
            self.error.append(f"Overview Record not insert Program Name: {response.meta.get('program_name', '')} error: {e}")

    def get_program_schedule_detail(self, response, included):
        try:
            thing = included[1].get('attributes', {})

            require_previous_gme = thing.get('field_previous_gme_years', '')
            step_2_required = thing.get('field_usmle_step_2_required', '')
            step_2_pass_required = thing.get('field_usmle_step2_req_int', '')
            level_1_required_do = self.check_no(thing.get('field_comlex_level_1', ''))
            ft_female_faculty = thing.get('field_pct_ft_female', '')
            ratio_of_ft_paid_faculty_to_positions = thing.get('field_ratio_ft_faculty', '')
            minimum_level_1_score_do = thing.get('field_comlex_level_1_score', '')
            step_1_pass_required = thing.get('field_usmle_step1_req_int', '')
            latest_application_date_2024_2025 = thing.get('field_latest_date_current_year', '')
            level_1_pass_required_do = thing.get('field_comlex_lvl1_req_int', '')

            interview_period_start_2024_2025 = self.get_value_end_value_for_program_schedule(thing,
                                                                                             'field_interview_period_curr_year',
                                                                                             'value')
            interview_period_stop_2024_2025 = self.get_value_end_value_for_program_schedule(thing,
                                                                                            'field_interview_period_curr_year',
                                                                                            'end_value')
            earliest_application_date_2025_2026 = self.get_value_end_value_for_program_schedule(thing,
                                                                                                'field_application_period',
                                                                                                'value')
            latest_application_date_2025_2026 = self.get_value_end_value_for_program_schedule(thing,
                                                                                              'field_application_period',
                                                                                              'end_value')
            interview_period_start_2025_2026 = self.get_value_end_value_for_program_schedule(thing,
                                                                                             'field_interview_period_next_year',
                                                                                             'value')
            interview_period_stop_2025_2026 = self.get_value_end_value_for_program_schedule(thing,
                                                                                            'field_interview_period_next_year',
                                                                                            'end_value')

            item = OrderedDict()
            item['Program ID'] = thing.get('field_program_id', '')
            item = self.get_year_positions(item, thing)
            item['Requires Previous GME'] = 'Yes' if require_previous_gme and require_previous_gme is not None else 'No'
            item['Offers Preliminary Positions'] = thing.get('field_offers_preliminary_positio', '')
            item['Participates in NRMP Main Match'] = thing.get('field_match_nrmp_main', '')
            item['Main Match Codes'] = self.get_main_match_codes(thing, 1)
            item['Participates in NRMP Advanced or Fellowship Match'] = thing.get('field_match_nrmp_adv_fellow', '')
            item['Advanced Match Codes'] = self.get_main_match_codes(thing, 0)
            item['Latest Application Date 2024-2025'] = self.convert_date_to_american_format(
                latest_application_date_2024_2025) if latest_application_date_2024_2025 else None
            item['Interview Period START 2024-2025'] = self.convert_date_to_american_format(
                interview_period_start_2024_2025) if interview_period_start_2024_2025 else None
            item['Interview Period STOP 2024-2025'] = self.convert_date_to_american_format(
                interview_period_stop_2024_2025) if interview_period_stop_2024_2025 else None
            item['Earliest Application Date 2025-2026'] = self.convert_date_to_american_format(
                earliest_application_date_2025_2026) if earliest_application_date_2025_2026 else None
            item['Latest Application Date 2025-2026'] = self.convert_date_to_american_format(
                latest_application_date_2025_2026) if latest_application_date_2025_2026 else None
            item['Interview Period START 2025-2026'] = self.convert_date_to_american_format(
                interview_period_start_2025_2026) if interview_period_start_2025_2026 else None
            item['Interview Period STOP 2025-2026'] = self.convert_date_to_american_format(
                interview_period_stop_2025_2026) if interview_period_stop_2025_2026 else None
            item['Remote Interview Option'] = thing.get('field_video_interview', '')
            item['Interviews Last Year'] = thing.get('field_interviews_conducted', '')

            interview_position_ratio = [data['attributes'].get('field_avg_pct_train_ambulatory', '') for data in response.json().get('included', [{}]) if data['attributes'].get('field_avg_pct_train_ambulatory', '')]
            item['Interview to Position Ratio'] = f"{' '.join(interview_position_ratio)} to 1" if interview_position_ratio else None

            item['Participates in SF Match'] = thing.get('field_participates_sf_match', '')
            item['Participates in Other Matching Program'] = thing.get('field_participates_other_match', '')
            item['Required Letters of Recommendation'] = thing.get('field_required_letters', '')
            item['Osteopathic Recognition'] = thing.get('field_or_acgme_aoa', '')
            item['Step 1 Required'] = thing.get('field_usmle_step_1_required', '')
            item['Step 1 Minimum Score'] = thing.get('field_usmle_step_1_minimum_score', '')
            item['Step 1 Pass Required'] = step_1_pass_required if step_1_pass_required else False
            item['Step 2 Required'] = 'Yes' if step_2_required else 'No'
            item['Step 2 Pass Required'] = 'Yes' if step_2_pass_required else 'No'
            item['Level 1 Required (DO)'] = 'Yes' if level_1_required_do else 'No'
            item['Minimum Level 1 Score (DO)'] = int(minimum_level_1_score_do) if minimum_level_1_score_do else None
            item['Level 1 Pass Required (DO)'] = level_1_pass_required_do if level_1_pass_required_do else False
            item['Level 2 Required (DO)'] = self.check_no(thing.get('field_comlex_level_2', ''))
            item['Level 2 Pass Required (DO)'] = thing.get('field_comlex_lvl2_req_int', False)
            item['PGY1 Med School Grad Recency'] = thing.get('field_years_since_graduation', None)
            item['PGY1 Experience Requirement During Gap'] = thing.get('field_medical_education_gap', '')
            item = self.get_visa_data(item, thing)

            item['Faculty Full Time MD'] = int(thing.get('field_total_physician', 0)) - int(
                thing.get('field_part_time_paid_physicians', 0))
            item['Faculty Part Time MD'] = int(thing.get('field_total_non_physician', 0)) - int(
                thing.get('field_part_time_paid_non_physici', 0))
            item['Faculty Full Time Non-MD'] = thing.get('field_part_time_paid_physicians', 0)
            item['Faculty Part Time Non-MD'] = thing.get('field_part_time_paid_non_physici', 0)
            item['Total MD Faculty'] = int(item['Faculty Full Time MD']) + int(item['Faculty Part Time MD'])
            item['Total  Non-MD Faculty'] = int(item['Faculty Full Time Non-MD']) + int(
                item['Faculty Part Time Non-MD'])
            item['% FT Female Faculty'] = "{:.2f}%".format(float(ft_female_faculty)) if ft_female_faculty else None
            item['Ratio of FT Paid Faculty to Positions'] = float("{:.2f}".format(
                float(ratio_of_ft_paid_faculty_to_positions))) if ratio_of_ft_paid_faculty_to_positions else None
            item['Avg Hours per Week (1st Year)'] = thing.get('field_avg_hours_on_duty_y1', '')
            item['Max Consecutive Hours (1st Year)'] = thing.get('field_max_hours_on_duty_y1', '')
            item['Avg Off Duty Periods per Week (1st Year)'] = float("{:.2f}".format(float(thing.get('field_avg_24hr_off_duty_y1', '')))) if thing.get(
                'field_avg_24hr_off_duty_y1', '') else None
            item['Moonlighting Allowed'] = thing.get('field_allows_moonlighting', '')
            item['Night Float System'] = thing.get('field_night_float', '')

            item['USMD Percentage'] = "{:.2f}%".format(float(thing.get('field_pct_usmd', ''))) if thing.get(
                'field_pct_usmd', '') else None
            item['IMG Percentage'] = "{:.2f}%".format(float(thing.get('field_pct_img', ''))) if thing.get(
                'field_pct_img', '') else None
            item['DO Percentage'] = "{:.2f}%".format(float(thing.get('field_pct_do', ''))) if thing.get('field_pct_do',
                                                                                                        '') else None
            item['Female Residents Percentage'] = "{:.2f}%".format(
                float(thing.get('field_pct_female', ''))) if thing.get('field_pct_female', '') else None
            item['Male Residents Percentage'] = "{:.2f}%".format(float(thing.get('field_pct_male', ''))) if thing.get(
                'field_pct_male', '') else None
            item = self.get_call_schedule(item, thing)
            item = self.get_beeper_or_home(item, thing)
            # item['Link to Program List'] = response.meta.get('program_id', '')
            item['Link to Program List'] = ''

            self.programworkschedule_counter += 1
            print(f"Programs Work Schedule Counter : {self.programworkschedule_counter}")
            self.table_programworkschedule_records.append(item)
        except Exception as e:
            self.error.append(
                f"Program & Work Schedule Record not insert : {response.meta.get('program_name', '')} error: {e}")

    def get_features_and_benefits(self, response, included):
        try:
            thing = included[1].get('attributes', {})
            training_in_non_hospital_community_based_settings_1st_year = self.non_hospital_community_based(thing.get('field_train_ambulatory_nonhospit', ''))
            if 'n/a' in str(training_in_non_hospital_community_based_settings_1st_year).lower() or 'N/A' in str(training_in_non_hospital_community_based_settings_1st_year):
                training_in_non_hospital_community_based_settings_1st_year = 'N/A'
            else:
                training_in_non_hospital_community_based_settings_1st_year = None

            salary_paid_by_non_profit_institution = thing.get('field_salary_paid_nonprofit', '')

            item = OrderedDict()
            item['Program ID'] = thing.get('field_program_id', '')
            item['Avg Structured Didactic Hours Per Week'] = thing.get('field_avg_hrs_lecture_conf_y1', '')
            item['Training in Hospital Outpatient Clinics (1st Year)'] = thing.get('field_training_outpatient_clinic', None)
            item['Training in Non-Hospital Community-Based Settings (1st Year)'] = training_in_non_hospital_community_based_settings_1st_year

            item = self.get_salary_vocation_sick_days(item, thing)

            item['Salary Paid by Non-profit Institution'] = True if salary_paid_by_non_profit_institution else False
            item['Max Paid Family Medical Leave Days'] = self.check_ngo(thing.get('field_leave_paid', ''))
            item['Max Unpaid Family Medical Leave Days'] = self.check_ngo(thing.get('field_leave_unpaid', ''))
            item['Leave Policies URL'] = thing.get('field_xpp_policy_leave_url', '')

            item = self.get_employment_policies_and_benefits(item, thing)

            item['Additional Training Opportunities'] = 'field_special_tracks'

            item = self.get_educational_features(item, thing)

            item = self.get_resident_evaluation(item, thing)

            item['Major Medical Insurance (Residents)'] = 'Fully Paid'
            item['Major Medical Insurance (Dependents)'] = 'Fully Paid'
            item['Major Medical Insurance (Domestic Partners)'] = 'Fully Paid'
            item['Outpatient Mental Health Insurance'] = 'Fully Paid'
            item['Inpatient Mental Health Insurance'] = 'Fully Paid'
            item['Group Life Insurance'] = 'Fully Paid'
            item['Dental Insurance'] = 'Fully Paid'
            item['Disability Insurance'] = 'Fully Paid'
            item['Disability Insurance for HIV'] = 'Not Available'

            item = self.get_educational_benefits(item, thing)

            item['Research Rotation'] = thing.get('field_research_rotation', '')

            item = self.get_program_evaluation(item, thing)

            # item['Link to Program List'] = response.meta.get('program_id', '')
            item['Link to Program List'] = ''

            self.featuresbenefits_counter += 1
            print(f"Features Benefits Counter : {self.featuresbenefits_counter}")
            self.table_featuresbenefits_records.append(item)
        except Exception as e:
            self.error.append(
                f"Features & Benefits Record not insert : {response.meta.get('program_name', '')} error: {e}")

    def get_value_from_included(self, included, attributes_name):
        return included.get('attributes', {}).get(attributes_name, '')

    def get_participant_institution_url_from_included(self, include, index):
        try:
            return include[index].get('attributes', {}).get('metatag_normalized', [])[2].get('attributes').get(
                'href')

        except IndexError:
            return ''

    def get_participant_institution_address_from_included(self, included, index):
        try:
            value = included[index].get('attributes', {})

        except IndexError:
            return ''

        address = value.get('field_address', {})

        if value.get('title', ''):
            return (f"{value.get('title', '')} {address.get('address_line1', '')}, {address.get('locality', '')}"
                    f", {address.get('administrative_area', '')} {address.get('postal_code', '')}")

        return ''

    def get_person_name_from_included(self, included):
        try:
            value = included.get('attributes', {})

        except IndexError:
            return
        if value.get('field_middle_name', ''):
            return (f"{value.get('field_first_name', '')} {value.get('field_middle_name', '')}"
                    f" {value.get('field_last_name', '')} {value.get('field_degrees', '')}")
        return (
            f"{value.get('field_first_name', '')} {value.get('field_last_name', '')}"
            f" {value.get('field_degrees', '')}")

    def get_person_information_from_included(self, included):
        try:
            value = included.get('attributes', {}).get('field_address', {})

        except IndexError:
            return

        return (f"{value.get('address_line2', '')}, {value.get('locality', '')}, {value.get('administrative_area', '')}"
                f" {value.get('postal_code', '')}")

    def get_location_from_included(self, included):
        try:
            value = included.get('attributes', {}).get('field_address', {})

        except IndexError:
            return

        return (f"{value.get('organization', '')} {value.get('address_line1', '')} {value.get('address_line2', '')}"
                f" {value.get('locality', '')}, {value.get('administrative_area', '')} {value.get('postal_code', '')}")

    def get_program_start_included(self, included):
        date_of_months = []
        months = included[1].get('attributes', {}).get('field_program_start_dates', [])

        for month in months:
            date_of_month = included[1].get('attributes', {}).get(f'field_start_date_{month.lower()}', '')

            if date_of_month:
                date_of_months.append(f"{month} {date_of_month}")

        return ' '.join(date_of_months)

    def check_video_availability(self, included):
        video = self.get_value_from_included(included[1], 'field_resource_video_desc_1')

        if not video:
            video = 'Not Available'

        return video

    def get_value_from_data(self, data, attributes_name):
        return data.get('attributes', {}).get(attributes_name, '')

    def get_year_positions(self, item, thing):
        thing = thing.get('field_program_size', [])

        for i in range(6):
            try:
                item[f'Year {i + 1} Positions'] = thing[i]
            except IndexError:
                item[f'Year {i + 1} Positions'] = 0

        return item

    def check_none(self, data):
        return int(data) if data and data.isdigit() else None

    def get_call_schedule(self, item, thing):
        thing = thing.get('field_call_schedule', [])
        # a = 'Every fourth night for 7 months'
        for i in range(0, 6):
            try:
                if thing[i].get('value', '') != 'N/A':
                    temporary = f"{thing[i].get('value', '')} for {thing[i].get('duration', '')} months"
                    item[f'Call Schedule Year {i + 1}'] = temporary
                else:
                    item[f'Call Schedule Year {i + 1}'] = 'Not Applicable'

            except IndexError:
                item[f'Call Schedule Year {i + 1}'] = 'Not Applicable'

        return item

    def get_beeper_or_home(self, item, thing):
        thing = thing.get('field_beeper_home_call', [])
        for i in range(1, 6):
            try:
                if thing[i] == 99 or thing[i] == '99':
                    item[f'Beeper or Home Call Year {i + 1}'] = 'NGO'
                else:
                    value = thing[i]
                    item[f'Beeper or Home Call Year {i + 1}'] = str(value)

            except IndexError:
                item[f'Beeper or Home Call Year {i}'] = 'NGO'

        return item

    def get_visa_data(self, item, thing):
        item['J-1 Visa Sponsorship'] = False
        item['H-1B Visa'] = False
        item['F-1 Visa (OPT)'] = 'No'

        for visa in thing.get('field_visa_status', []):
            if re.compile(r'J-1', re.IGNORECASE).search(visa):
                item['J-1 Visa Sponsorship'] = True

            if re.compile(r'H-1B', re.IGNORECASE).search(visa):
                item['H-1B Visa'] = True

            if re.compile(r'F-1', re.IGNORECASE).search(visa):
                item['F-1 Visa (OPT)'] = 'Yes'

        return item

    def check_government_affiliation(self, data):
        pattern = re.compile(r'Not', re.IGNORECASE)

        if pattern.search(data):
            return 'No'
        else:
            return 'Yes'

    def extract_date(self, data):
        if data:
            pattern = re.compile(r'(\d{4}-\d{2}-\d{2})')
            match = pattern.search(data)

            if match:
                return match.group(1)
            else:
                return ''

        return ''

    def check_no(self, data):
        if data:
            pattern = re.compile(r'No', re.IGNORECASE)

            if pattern.search(data):
                return 'No'
            else:
                return 'Yes'

        return 'No'

    def get_main_match_codes(self, thing, index):
        try:
            return thing.get('field_match_nrmp_codes', [])[index]
        except IndexError:
            return ''

    def get_value_end_value_for_program_schedule(self, thing, selector, value):
        try:
            return thing.get(selector, {}).get(value, '')
        except AttributeError:
            return ''

    def non_hospital_community_based(self, thing):
        if thing == 999 or thing == '999':
            return 'N/A'

        return thing

    def get_salary_vocation_sick_days(self, item, thing):
        data_dict = thing.get('field_graduate_year_statistics', [])
        data_dict = [item for item in data_dict if item.get('salary') or item.get('paid_sick')]
        for i in range(0, 4):
            try:
                temporary = data_dict[i]
                salary = temporary.get('salary', '')
                formatted_salary = "${:,.2f}".format(salary) if salary else None
                item[f'Salary Year {i + 1}'] = formatted_salary
                item[f'Vacation Days Year {i + 1}'] = temporary.get('paid_vacation', None)
                item[f'Sick Days Year {i + 1}'] = temporary.get('paid_sick', '')
            except IndexError:
                item[f'Salary Year {i + 1}'] = ''
                item[f'Vacation Days Year {i + 1}'] = None
                item[f'Sick Days Year {i + 1}'] = None

        return item

    def check_ngo(self, thing):
        if thing == 999 or thing == '999':
            return 'NGO'

        return str(thing)

    def get_employment_policies_and_benefits(self, item, thing):
        item['Part-time/Shared Schedule Positions'] = 'No'
        item['On-site Child Care'] = 'No'
        item['Subsidized Child Care'] = 'No'
        item['Moving Allowance'] = False
        item['Housing Stipend'] = False
        item['Free Parking'] = 'No'
        item['On-call Meal Allowance'] = False
        item['Technology Allowance'] = False
        item['Placement Assistance'] = False
        item['Policy Prohibits Hiring Smokers'] = 'No'

        temporary = thing.get('field_program_offers_2021', [])

        for i in range(10):
            try:
                if temporary[i] == "Part-time/shared schedule positions":
                    item['Part-time/Shared Schedule Positions'] = 'Yes'

                elif temporary[i] == "On-site child care":
                    item['On-site Child Care'] = 'Yes'

                elif temporary[i] == "Subsidized child care":
                    item['Subsidized Child Care'] = 'Yes'

                elif temporary[i] == "Moving allowance":
                    item['Moving Allowance'] = True

                elif temporary[i] == "Housing stipend":
                    item['Housing Stipend'] = True

                elif temporary[i] == "Free parking":
                    item['Free Parking'] = 'Yes'

                elif temporary[i] == "On-call meal allowance":
                    item['On-call Meal Allowance'] = True

                elif temporary[i] == "iPads, tablets, etc., or technology allowance":
                    item['Technology Allowance'] = True

                elif temporary[
                    i] == "Placement assistance upon completion of program into practice, fellowship or academia":
                    item['Placement Assistance'] = True

                elif 'Policy Prohibits Hiring Smokers' in temporary[i]:
                    item['Policy Prohibits Hiring Smokers'] = 'Yes'
                else:
                    a = ''
            except IndexError:
                break

        return item

    def get_educational_features(self, item, thing):
        item['Additional Training Opportunities'] = 'No'
        item['Primary Care Track'] = 'No'
        item['Rural Track'] = 'No'
        item["Women's Health Track"] = 'No'
        item['Hospitalist Track'] = 'No'
        item['Research Track'] = False
        item['Academic or Clinician Educator Track'] = False
        item['Other Track'] = 'No'

        temporary = thing.get('field_special_tracks', [])

        for i in range(8):
            try:
                if temporary[i] == "":
                    item['Additional Training Opportunities'] = 'Yes'

                elif temporary[i] == "Primary care":
                    item['Primary Care Track'] = 'Yes'

                elif temporary[i] == "Rural":
                    item['Rural Track'] = 'Yes'

                elif temporary[i] == "Women's health":
                    item["Women's Health Track"] = 'Yes'

                elif temporary[i] == "Hospitalist":
                    item['Hospitalist Track'] = 'Yes'

                elif temporary[i] == "Research track/fellowship (non-ACGME accredited)":
                    item['Research Track'] = True

                elif temporary[i] == 'Academic or clinician educator':
                    item['Academic or Clinician Educator Track'] = True

                elif temporary[i] == "special_track_academic_clinician":
                    item['Other Track'] = 'Yes'

                else:
                    a = ''

            except IndexError:
                break

        return item

    def get_resident_evaluation(self, item, thing):
        item['Patient Surveys'] = False
        item['Portfolio System'] = False
        item['OSCE'] = False

        temporary = thing.get('field_evaluate_res_fellow_2019', [])

        for i in range(4):
            try:
                if temporary[i] == 'Patient surveys':
                    item['Patient Surveys'] = True

                elif temporary[i] == 'Portfolio system':
                    item['Portfolio System'] = True

                elif temporary[i] == 'Objective structured clinical examinations (OSCE)':
                    item['OSCE'] = True

                else:
                    a = ''

            except IndexError:
                break

        return item

    def convert_bool_to_yes_no(self, data):
        # if data == False:
        if not data:
            return 'No'

        elif data:
            return 'Yes'
        # else:
        #     return data

    def get_educational_benefits(self, item, thing):
        item['Integrative Medicine Curriculum'] = False
        item['Health Systems Leadership Curriculum'] = False
        item['Interprofessional Teamwork'] = False
        item['Medical Spanish Instruction'] = 'No'
        item['Alternative Medicine Curriculum'] = False
        item['Health Care Systems Economics Curriculum'] = False
        item['Debt Management Counseling'] = False
        item['USMLE Step 3 Academic Support'] = 'No'
        item['International Experience'] = False
        item['Resident/Fellow Retreats'] = False
        item['Off-campus Electives'] = False
        item['Hospice/Home Care Experience'] = 'No'
        item['Advanced Degree Training'] = False

        temporary = thing.get('field_resident_fellow_offer_2019', [])

        for i in range(0, 13):
            try:
                if temporary[i] == 'Integrative medicine curriculum':
                    item['Integrative Medicine Curriculum'] = True

                elif temporary[i] == ('Curriculum to develop health systems leadership skills (e.g., QI project '
                                      'leadership, community/organizational advocacy)'):
                    item['Health Systems Leadership Curriculum'] = True

                elif temporary[i] == 'Formal program to foster interprofessional teamwork':
                    item['Interprofessional Teamwork'] = True

                elif temporary[i] == "Instruction in medical Spanish or other non-English language":
                    item['Medical Spanish Instruction'] = 'Yes'

                elif temporary[i] == 'Alternative/complementary medicine curriculum':
                    item['Alternative Medicine Curriculum'] = True

                elif temporary[i] == 'Economics of health care systems curriculum':
                    item['Health Care Systems Economics Curriculum'] = True

                elif temporary[i] == 'Debt management/financial counseling':
                    item['Debt Management Counseling'] = True

                elif temporary[i] == "Academic support for USMLE Step 3 preparation":
                    item['USMLE Step 3 Academic Support'] = 'Yes'

                elif temporary[i] == 'International experience/global health':
                    item['International Experience'] = True

                elif temporary[i] == 'Resident/fellow retreats':
                    item['Resident/Fellow Retreats'] = True

                elif temporary[i] == 'Off-campus electives':
                    item['Off-campus Electives'] = True

                elif temporary[i] == "Hospice/home care experience":
                    item['Hospice/Home Care Experience'] = 'Yes'

                elif temporary[i] == 'MPH, MBA, PhD or other advanced degree training':
                    item['Advanced Degree Training'] = True

                else:
                    a = ''
            except IndexError:
                break

        return item

    def get_program_evaluation(self, item, thing):
        item['Aggregate Milestone Achievements'] = False
        item['Board Certification Pass Rates'] = False
        item['Performance-based Assessment Scores'] = False

        temporary = thing.get('field_program_evaluation_2019', [])

        for i in range(0, 3):
            try:
                if 'Aggregate resident Milestone achievements' in temporary[i]:
                    item['Aggregate Milestone Achievements'] = True

                elif temporary[i] == 'Graduates’ board certification pass rates':
                    item['Board Certification Pass Rates'] = True

                elif temporary[i] == 'Performance-based assessment scores (e.g. OSCE, patient or computer simulations)':
                    item['Performance-based Assessment Scores'] = True

                else:
                    a = ''

            except IndexError:
                break

        return item

    def convert_date_to_american_format(self, date):
        year, month, day = date.split('-')
        format_date = f"{month}/{day}/{year}"

        return format_date

    def write_logs(self):
        log_folder = 'logs'
        os.makedirs(log_folder, exist_ok=True)
        with open(self.logs_filepath, mode='a', encoding='utf-8') as logs_file:
            for log in self.mandatory_logs:
                self.logger.info(log)
                logs_file.write(f'{log}\n')

            logs_file.write(f'\n\n')

    def close(spider, reason):
        upload_airtable_data(data=spider)
        spider.mandatory_logs.append(f'\nSpider "{spider.name}" was started at "{spider.current_dt}"')
        spider.mandatory_logs.append(f'Spider "{spider.name}" closed at "{datetime.now().strftime("%d%m%Y%H%M")}"\n\n')

        spider.mandatory_logs.append(f'Spider "{spider.name}" Records Founded at Website for Programs List Table : "{spider.programs_counter}"')
        spider.mandatory_logs.append(f'Spider "{spider.name}" Records Founded at Website for Overview records are : "{spider.overview_counter}"')
        spider.mandatory_logs.append(f'Spider "{spider.name}" Records Founded at Website for Program work Schedule Table : "{spider.programworkschedule_counter}"')
        spider.mandatory_logs.append(f'Spider "{spider.name}" Records Founded at Website for Features and Benefits Table : "{spider.featuresbenefits_counter}"\n\n')

        spider.mandatory_logs.append(f'Spider Error:: \n')
        spider.mandatory_logs.extend(spider.error)

        spider.write_logs()

