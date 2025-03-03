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


def main():
    images = 'input/Images to Move Into 2 Folders'

    output_folder = 'output'
    create_folder(output_folder)

    folder_1 = 'output/Image Files Batch 1'
    create_folder(folder_1)

    folder_2 = 'output/Image Files Batch 2'
    create_folder(folder_2)

    file_1 = 'input/Image File Names Batch 1.xlsx'
    file_2 = 'input/Image File Names Batch 2.xlsx'
    sheet = 'Sheet1'

    file_one = read_excel(file_1, sheet)
    file_two = read_excel(file_2, sheet)

    move_images(images, folder_1, file_one)
    move_images(images, folder_2, file_two)


if __name__ == '__main__':
    main()
