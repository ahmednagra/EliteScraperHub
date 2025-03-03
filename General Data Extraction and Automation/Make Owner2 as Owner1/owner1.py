import csv
import glob
import os


def process_csv(input_file):
    try:
        # Get the file name
        file_name = os.path.basename(input_file)

        # Read the CSV file and get the rows
        with open(input_file, 'r') as file:
            reader = csv.reader(file)
            rows = list(reader)

            # Extract header and data rows
            header = rows[0]
            data = rows[1:]

            # Process data rows
            processed_rows = []
            for row in data:
                # Skip if Number 1 column is empty
                if not row[10]:
                    continue

                # Process Owner1 and Owner2 fields
                owner1_fields = row[8:24]
                processed_row = row[:8] + owner1_fields
                processed_rows.append(processed_row)

        # Create the output folder if it doesn't exist
        output_folder = 'output'
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Create the output file path
        processed_file_name = file_name.replace('.csv', ' (Processed).csv')
        output_file_path = os.path.join(output_folder, processed_file_name)

        # Write the processed rows to the output CSV file
        with open(output_file_path, 'w', newline='') as output_file:
            writer = csv.writer(output_file)
            writer.writerow(header[:24])
            writer.writerows(processed_rows)

        print(f"Processing of {file_name} successful.")
        return True

    except Exception as e:
        print(f"Error processing {input_file}: {e}")
        return False


if __name__ == "__main__":
    # Get a list of input files
    input_files = glob.glob('input/*.csv')

    # Process each input file
    for input_file in input_files:
        process_csv(input_file)
