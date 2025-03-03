import csv
import os
import re
from datetime import datetime
import glob
import fitz  # PyMuPDF


def extract_date_time(file_name):
    pattern = re.compile(r'(\d{8})_(\d{6})|(\d{8})(\d{6})|(\d{8})')
    try:
        match = pattern.search(file_name)
        if match:
            date_str = match.group(1) or match.group(3) or match.group(5)
            time_str = match.group(2) or match.group(4) or '000000'
            date_time_str = date_str + time_str
            date_time_obj = datetime.strptime(date_time_str, '%Y%m%d%H%M%S')
            date_time_component = date_time_obj.strftime('%Y%m%d %H%M%S')
            return date_time_component
        else:
            print(f"Error: Date/Time format not found in filename: {file_name}")
            return None
    except Exception as e:
        print(f"Error extracting date/time from filename: {file_name} - {e}")
        return None


def process_pdf(input_file):
    try:
        date = extract_date_time(input_file)
        doc = fitz.open(input_file)
        all_text = []
        # Check the first two pages
        for page_num in range(min(2, doc.page_count)):
            page = doc.load_page(page_num)
            page_text = page.get_text("text")
            if page_text.strip():  # If the text is not empty
                all_text.append(page_text)
                break  # Exit the loop after finding the first non-empty page

        combined_text = "\n".join(all_text).strip()
        pattern = r'JUDICIAL COUNCIL COORDINATION(.*)'
        second_pattern = r'Case No'
        match = re.search(pattern, combined_text, re.DOTALL) or re.search(second_pattern, combined_text, re.DOTALL)
        case_info = ''
        if match:
            extracted_text = match.group(1).strip()
            case_info = ''.join(
                ''.join(extracted_text.split('Master Complaint Filed')[0:1]).split('DATE:')[0:1]).strip()
            case_info = ''.join(case_info.split(']')[1:]).strip()
        write_csv(date, combined_text, case_info)
    except Exception as e:
        print(f"Error processing PDF file: {input_file} - {e}")


def write_csv(date, info_text, case_info):
    try:
        os.makedirs('output', exist_ok=True)
        filepath = f'output/Case Information {datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.csv'
        with open(filepath, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if csvfile.tell() == 0:
                writer.writerow(['Date', 'Information', 'Case Information'])
            writer.writerow([date, info_text, case_info])
    except Exception as e:
        print(f"Error writing to CSV", e)


if __name__ == "__main__":
    input_files = glob.glob('input/*.pdf')
    for input_file in input_files:
        process_pdf(input_file)
