import glob
import os


def search_word_in_files(word):
    filenames = glob.glob('**/*.py', recursive=True)
    for filename in filenames:
        with open(filename, 'r', encoding='utf-8', errors='ignore') as file:
            file_content = file.read()
            if word in file_content:
                print(f"Word '{word}' found in file: {filename}")


# Example usage:
search_word_in_files("googlesheet")
a = 1
