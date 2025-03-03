import os
import csv
import glob


def create_directory(name):
    try:
        os.makedirs(name, exist_ok=True)
        print(f"Directory created: {name}")
    except OSError as e:
        print(f"Error creating directory {name}: {e}")


def process_year(year, output_dir, input_dir):
    year_str = str(year)
    year_output_dir = os.path.join(output_dir, year_str)
    create_directory(name=year_output_dir)

    non_hvac_year_file = os.path.join(year_output_dir, 'Non_HVAC_Permits.csv')
    hvac_year_file = os.path.join(year_output_dir, 'HVAC_Permits.csv')

    non_hvac_files = glob.glob(os.path.join(input_dir, 'Non HVAC Permits', year_str, '*.csv'))
    hvac_files = glob.glob(os.path.join(input_dir, 'Permits Details', year_str, '*.csv'))

    if non_hvac_files:
        print(f"Processing Non-HVAC files for year {year}: Total files are: {len(non_hvac_files)}")
        sorted_non_hvac_file = sorted(non_hvac_files, key=sort_key)
        merge_csv_files(sorted_non_hvac_file, non_hvac_year_file)

    if hvac_files:
        print(f"Processing HVAC files for year {year}: Total files are: {len(hvac_files)}")
        sorted_hvac_file = sorted(hvac_files, key=sort_key)
        merge_csv_files(sorted_hvac_file, hvac_year_file)


def merge_csv_files(file_list, output_file, encoding='utf-8'):
    header_saved = False
    try:
        with open(output_file, 'w', newline='', encoding=encoding) as output_csv_file:
            writer = csv.writer(output_csv_file)
            for filename in file_list:
                try:
                    with open(filename, 'r', encoding=encoding) as csv_file:
                        reader = csv.reader(csv_file)
                        header = next(reader)
                        if not header_saved:
                            writer.writerow(header)
                            header_saved = True
                        for row in reader:
                            writer.writerow(row)
                except UnicodeDecodeError as e:
                    print(f"UnicodeDecodeError: {e}. Skipping file: {filename}")
        print(f"Merged CSV file created: {output_file}")
    except Exception as e:
        print(f"Error merging CSV files: {e}")


def sort_key(file_path):
    try:
        base_name = os.path.basename(file_path)
        parts = base_name.split('_')
        month = parts[0]
        year_value = parts[1].split('.')[0]
        return int(year_value), int(month)
    except (IndexError, ValueError) as e:
        print(f"Error sorting file {file_path}: {e}")
        return 0, 0  # Return a default value that won't disrupt sorting


def main():
    input_dir = './output'
    output_dir = './Merged'

    # Create two Folders: 1 - All, 2 - Year Wise
    all_dir = os.path.join(output_dir, 'All')
    year_wise_dir = os.path.join(output_dir, 'Year Wise')
    create_directory(name=all_dir)
    create_directory(name=year_wise_dir)

    # The "All" folder should have 2 CSV files
    non_hvac_all_file = os.path.join(all_dir, 'Non_HVAC_Permits.csv')
    hvac_all_file = os.path.join(all_dir, 'HVAC_Permits.csv')

    # Get all records from previous files of Non Hvac Permits and permits Details
    records_non_hvac_files = glob.glob(os.path.join(input_dir, 'Non HVAC Permits', '*', '*.csv'))
    records_hvac_files = glob.glob(os.path.join(input_dir, 'Permits Details', '*', '*.csv'))

    if records_non_hvac_files:
        print(f"\n\nFound Non-HVAC Permits files: {len(records_non_hvac_files)}")
        non_hvac_files_sorted = sorted(records_non_hvac_files, key=sort_key)
        merge_csv_files(non_hvac_files_sorted, non_hvac_all_file)

    if records_hvac_files:
        print(f"\n\nFound Permits files: {len(records_hvac_files)}")
        hvac_files_sorted = sorted(records_hvac_files, key=sort_key)
        merge_csv_files(hvac_files_sorted, hvac_all_file)

    # Create yearly base folders in the Merged folder
    non_hvac_years = [os.path.basename(d) for d in glob.glob(os.path.join(input_dir, 'Non HVAC Permits', '*')) if
                      os.path.isdir(d)]
    hvac_years = [os.path.basename(d) for d in glob.glob(os.path.join(input_dir, 'Permits Details', '*')) if
                  os.path.isdir(d)]

    # Ensure we only process years that are valid
    years = sorted(set(non_hvac_years).union(hvac_years))

    for year in years:
        print(f"\n\nProcessing year: {year}")
        process_year(year=year, output_dir=year_wise_dir, input_dir=input_dir)


if __name__ == "__main__":
    main()

