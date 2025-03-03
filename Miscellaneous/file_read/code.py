
import csv

file_path = 'input/2019 to 2023 Gwinnett Tax Sale Results.csv'  # Replace with the path to your CSV file
data = []

try:
    with open(file_path, 'r') as csv_file:
        csv_reader = csv.reader(csv_file)
        data = list(csv_reader)
except FileNotFoundError:
    print(f"File '{file_path}' not found.")
except Exception as e:
    print(f"An error occurred: {str(e)}")

print(data)
