import os
import shutil
import openpyxl


def create_folder(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"Created folder: {folder}")


def read_excel(filepath, sheet):
    try:
        # Load the workbook
        workbook = openpyxl.load_workbook(filepath)

        # Select the desired sheet
        sheet = workbook[sheet]

        # Extract data from the sheet and store it in a list
        result_list = [str(cell.value) for cell in sheet['A']]

        return result_list

    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def move_images(source_folder, destination_folder, file_names):
    os.makedirs(destination_folder, exist_ok=True)

    for file_name in file_names:
        source_path = os.path.join(source_folder, file_name)
        destination_path = os.path.join(destination_folder, file_name)

        try:
            shutil.move(source_path, destination_path)
            print(f"Moved {file_name} to {destination_folder}")
        except FileNotFoundError:
            print(f"File not found: {file_name}")
