import method


def main():
    images = 'input/Images to Move Into 2 Folders'

    output_folder = 'output'
    method.create_folder(output_folder)

    folder_1 = 'output/Image Files Batch 1'
    method.create_folder(folder_1)

    folder_2 = 'output/Image Files Batch 2'
    method.create_folder(folder_2)

    file_1 = 'input/Image File Names Batch 1.xlsx'
    file_2 = 'input/Image File Names Batch 2.xlsx'
    sheet = 'Sheet1'

    file_one = method.read_excel(file_1, sheet)
    file_two = method.read_excel(file_2, sheet)

    method.move_images(images, folder_1, file_one)
    method.move_images(images, folder_2, file_two)


if __name__ == '__main__':
    main()
