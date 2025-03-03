import csv
import os

from openpyxl import Workbook
from nameparser import HumanName


def process_data(file_path):
    data = []

    try:
        with open(file_path, 'r') as csv_file:
            csv_reader = csv.DictReader(csv_file)
            data = list(csv_reader)
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")
        return
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return

    items_list = []

    for row in data:
        item = {}
        item['Tax auction date'] = row['Tax Sale Date']
        item['Parcel id'] = row['Parcel']
        item['Mailing address'] = row['Situs']
        name = HumanName(row['OwnerName'])
        item['First Name'] = name.first
        item['Last Name'] = name.last
        item['Status'] = row['Status']
        item['Last sale price'] = row['Amount Due']
        items_list.append(item)

    field_names = {
        'First Name': '', 'Last Name': '', 'Mailing address': '', 'Mailing city': '', 'Mailing state': '',
        'Mailing zip': '',
        'Mailing zip5': '', 'Mailing county': '', 'Mailing vacant': '', 'Property address': '', 'Property city': '',
        'Property state': '', 'Property zip': '', 'Property zip5': '', 'Property county': '', 'Property vacant': '',
        'Business Name': '', 'Status': '', 'Messages': '', 'Lists': '', 'Tags': '', 'Email 1': '', 'Email 2': '',
        'Email 3': '',
        'Email 4': '', 'Email 5': '', 'Email 6': '', 'Email 7': '', 'Email 8': '', 'Email 9': '', 'Email 10': '',
        'Phone 1': '',
        'Phone Type 1': '', 'Phone Status 1': '', 'Phone Tags 1': '', 'Phone 2': '', 'Phone Type 2': '',
        'Phone Status 2': '',
        'Phone Tags 2': '', 'Phone 3': '', 'Phone Type 3': '', 'Phone Status 3': '', 'Phone Tags 3': '', 'Phone 4': '',
        'Phone Type 4': '', 'Phone Status 4': '', 'Phone Tags 4': '', 'Phone 5': '', 'Phone Type 5': '',
        'Phone Status 5': '',
        'Phone Tags 5': '', 'Phone 6': '', 'Phone Type 6': '', 'Phone Status 6': '', 'Phone Tags 6': '', 'Phone 7': '',
        'Phone Type 7': '', 'Phone Status 7': '', 'Phone Tags 7': '', 'Phone 8': '', 'Phone Type 8': '',
        'Phone Status 8': '',
        'Phone Tags 8': '', 'Phone 9': '', 'Phone Type 9': '', 'Phone Status 9': '', 'Phone Tags 9': '', 'Phone 10': '',
        'Phone Type 10': '', 'Phone Status 10': '', 'Phone Tags 10': '', 'Phone 11': '', 'Phone Type 11': '',
        'Phone Status 11': '', 'Phone Tags 11': '', 'Phone 12': '', 'Phone Type 12': '', 'Phone Status 12': '',
        'Phone Tags 12': '', 'Phone 13': '', 'Phone Type 13': '', 'Phone Status 13': '', 'Phone Tags 13': '',
        'Phone 14': '',
        'Phone Type 14': '', 'Phone Status 14': '', 'Phone Tags 14': '', 'Phone 15': '', 'Phone Type 15': '',
        'Phone Status 15': '', 'Phone Tags 15': '', 'Phone 16': '', 'Phone Type 16': '', 'Phone Status 16': '',
        'Phone Tags 16': '', 'Phone 17': '', 'Phone Type 17': '', 'Phone Status 17': '', 'Phone Tags 17': '',
        'Phone 18': '',
        'Phone Type 18': '', 'Phone Status 18': '', 'Phone Tags 18': '', 'Phone 19': '', 'Phone Type 19': '',
        'Phone Status 19': '', 'Phone Tags 19': '', 'Phone 20': '', 'Phone Type 20': '', 'Phone Status 20': '',
        'Phone Tags 20': '', 'Phone 21': '', 'Phone Type 21': '', 'Phone Status 21': '', 'Phone Tags 21': '',
        'Phone 22': '',
        'Phone Type 22': '', 'Phone Status 22': '', 'Phone Tags 22': '', 'Phone 23': '', 'Phone Type 23': '',
        'Phone Status 23': '', 'Phone Tags 23': '', 'Phone 24': '', 'Phone Type 24': '', 'Phone Status 24': '',
        'Phone Tags 24': '', 'Phone 25': '', 'Phone Type 25': '', 'Phone Status 25': '', 'Phone Tags 25': '',
        'Phone 26': '',
        'Phone Type 26': '', 'Phone Status 26': '', 'Phone Tags 26': '', 'Phone 27': '', 'Phone Type 27': '',
        'Phone Status 27': '', 'Phone Tags 27': '', 'Phone 28': '', 'Phone Type 28': '', 'Phone Status 28': '',
        'Phone Tags 28': '', 'Phone 29': '', 'Phone Type 29': '', 'Phone Status 29': '', 'Phone Tags 29': '',
        'Phone 30': '',
        'Phone Type 30': '', 'Phone Status 30': '', 'Phone Tags 30': '', 'List Stack': '', 'Bedrooms': '',
        'Bathrooms': '',
        'Sqft': '', 'Air Conditioner': '', 'Heating type': '', 'Storeys': '', 'Year': '', 'Above grade': '',
        'Rental value': '',
        'Building use code': '', 'Neighborhood rating': '', 'Structure type': '', 'Number of units': '', 'Apn': '',
        'Parcel id': '', 'Legal description': '', 'Lot size': '', 'Land zoning': '', 'Tax auction date': '',
        'Total taxes': '', 'Tax delinquent value': '', 'Tax delinquent year': '', 'Year behind on taxes': '',
        'Deed': '',
        'Mls': '', 'Last sale price': '', 'Last sold': '', 'Lien type': '', 'Lien recording date': '',
        'Personal representative': '', 'Personal representative phone': '', 'Probate open date': '',
        'Attorney on file': '', 'Foreclosure date': '', 'Bankruptcy recording date': '', 'Divorce file date': '',
        'Loan to value': '', 'Open mortgages': '', 'Mortgage type': '', 'Owned since': '', 'Estimated value': '',
        'exported from REISift.io': ''
    }

    workbook = Workbook()
    sheet = workbook.active

    # Write the field names to the first row of the sheet
    sheet.append(list(field_names.keys()))

    # Write data to the sheet
    for item in items_list:
        row_values = [item.get(field_name, '') for field_name in field_names.keys()]
        sheet.append(row_values)

    # Save the workbook
    try:
        output_dir = 'output'
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, 'Description.xlsx')
        workbook.save(output_path)
        print(f"Data saved to '{output_path}'.")
    except Exception as e:
        print(f"An error occurred while saving the data: {str(e)}")


def main():
    file_path = os.path.join('input', '2019 to 2023 Gwinnett Tax Sale Results.csv')
    process_data(file_path)


if __name__ == '__main__':
    main()
