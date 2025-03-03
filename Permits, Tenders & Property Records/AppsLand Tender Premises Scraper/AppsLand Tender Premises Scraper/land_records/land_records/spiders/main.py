import os
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog
import json
import os.path
from collections import OrderedDict

from datetime import datetime
import logging
from scrapy.utils.log import configure_logging

import requests
import xlsxwriter
import shutil

configure_logging(install_root_handler=False)
logging.basicConfig(
    filename=f'logs.txt',
    format='%(levelname)s: %(message)s',
    level=logging.INFO,
    filemode='w'
)


class AppslandSpider:
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Connection': 'keep-alive',
        'Referer': 'https://apps.land.gov.il/MichrazimSite/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36',
    }

    def __init__(self, urls=None):
        self.urls = urls
        self.items = []
        self.parse_detail()

    def parse_detail(self):
        url_id = self.urls.split('/')[-1]
        search_url = f'https://apps.land.gov.il/MichrazimSite/api/MichrazDetailsApi/Get?michrazID={url_id}'
        response = requests.get(search_url, headers=self.headers)

        try:
            table_data = json.loads(response.text).get('Tik', [{}])
        except json.JSONDecodeError:
            return

        for row in table_data:
            item = OrderedDict()

            try:
                sub_table_1 = row.get('TochnitMigrash', [{}])[0]
                sub_table_2 = row.get('GushHelka', [{}])[0]
            except IndexError:
                sub_table_1 = {}
                sub_table_2 = {}
            except AttributeError:

                sub_table_1 = {}
                sub_table_2 = {}

            bid_numbers = [str(value.get('HatzaaSum', '')) for value in row.get('mpHatzaaotMitcham', [])] or []

            item['מספר מתחם'] = row.get('MitchamName', '')
            item['יח"ד'] = row.get('Kibolet', '')
            item['שם זוכה'] = row.get('ShemZoche', '')
            item['מחיר סופי ב₪'] = row.get('SchumZchiya', '')
            item['הוצאות פיתוח ב₪'] = row.get('HotzaotPituach', '')
            item['שטח במ"ר'] = row.get('Shetach', '')
            item['מחיר מינימום ב₪'] = row.get('MechirSaf', '')
            item['מחיר שומה ב₪'] = row.get('mechirShuma', '')
            item['תוכנית'] = sub_table_1.get('Tochnit', '')
            item['מגרש'] = sub_table_1.get('MigrashName', '')
            item['גוש'] = sub_table_2.get('Gush', '')
            item['חלקה'] = sub_table_2.get('Helka', '')
            item['סכום הצעה ב₪'] = ', '.join(bid_numbers)
            item[' Counts סכום הצעה ב₪'] = len(bid_numbers)
            item['Search URL'] = self.urls

            self.items.append(item)

        self.write_to_file()

    def write_to_file(self):
        columns = [x for x in self.items[0].keys()] if self.items else []
        output_dir = 'output'

        if not os.path.isdir(output_dir):
            os.makedirs(output_dir)

        # Create a workbook and add a worksheet.
        workbook = xlsxwriter.Workbook(f'{output_dir}/AppsLandTenderPremises.xlsx')
        worksheet = workbook.add_worksheet()

        row = 0
        for index, value in enumerate(columns):
            worksheet.write_string(row, index, value)

        for item in self.items:
            row += 1
            col = 0

            for value in item.values():
                value = str(value) if value else ''
                worksheet.write_string(row, col, value)
                col += 1

        workbook.close()
        logging.info("Data has been written to the file successfully.")


class SpiderGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Rami - Excel")
        self.configure(bg="#E0E0E0")
        self.create_widgets()

    def create_widgets(self):
        # Create a label for the title
        title_label = tk.Label(self, text="Rami - Excel", font=("Arial", 24, "bold"), fg="#FFFFFF", bg="#4B8BBE")
        title_label.pack(pady=20)

        # Create a frame for the input and buttons
        frame = tk.Frame(self, bg="#E0E0E0")
        frame.pack(padx=20, pady=10)

        # Create a label for the input field
        input_label = tk.Label(frame, text="Input:", font=("Arial", 12), fg="#000000", bg="#E0E0E0")
        input_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Create an entry field for the user input
        self.input_var = tk.StringVar()
        self.input_var.set("Kindly enter your URL")

        self.input_entry = tk.Entry(frame, font=("Arial", 12), width=30, textvariable=self.input_var)
        self.input_entry.grid(row=0, column=1, padx=5, pady=5)

        # Clear the placeholder text when the input field is clicked
        def clear_placeholder(event):
            current_text = self.input_entry.get()
            if current_text == "Kindly enter your URL":
                self.input_var.set("")
                self.input_entry.unbind("<FocusIn>")  # Unbind the event after clearing the text

        self.input_entry.bind("<FocusIn>", clear_placeholder)

        # Bind the Enter key press event to the Run button click
        self.input_entry.bind("<Return>", lambda event: run_button.invoke())

        # Function to handle key release events
        def _onKeyRelease(event):
            ctrl = (event.state & 0x4) != 0
            if event.keycode == 88 and ctrl and event.keysym.lower() != "x":
                event.widget.event_generate("<<Cut>>")

            if event.keycode == 86 and ctrl and event.keysym.lower() != "v":
                event.widget.event_generate("<<Paste>>")

            if event.keycode == 67 and ctrl and event.keysym.lower() != "c":
                event.widget.event_generate("<<Copy>>")

        # Bind the Ctrl + x, Ctrl + c, and Ctrl + v key combinations
        self.input_entry.bind("<KeyRelease>", _onKeyRelease)

        # Set the focus to the input field when the UI is opened
        self.input_entry.focus_set()


        def run_spider():
            input_value = self.input_entry.get()

            if not input_value:
                # Show a message box when the input is empty
                messagebox.showwarning("Empty Input", "Kindly enter the URL.")
                return

            try:
                AppslandSpider(input_value)

                # Show a message box when the spider completes
                messagebox.showinfo("Scraping Completed", "The spider has finished running.")
                self.download_button.config(state="normal")  # Enable the download button

            except Exception as e:
                # Show error message in a label
                error_label.config(text=str(e))
                logging.error(str(e))

        # Create a button to run the spider
        run_button = tk.Button(frame, text="Run", font=("Arial", 12, "bold"), fg="#FFFFFF", bg="#4B8BBE",
                               command=run_spider)
        run_button.grid(row=0, column=2, padx=5, pady=5)

        def download_result():
            try:
                # Get the file path to save the result
                default_filename = "AppsLandTenderPremises.xlsx"  # Default filename with extension
                file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=default_filename)
                base_dir = os.path.dirname(os.path.abspath(__file__))
                print('Base directory:', base_dir)

                # Copy the desired file to the specified location
                shutil.copy("output/AppsLandTenderPremises.xlsx", file_path)
                print('shutil.copy:', shutil.copy("output/AppsLandTenderPremises.xlsx", file_path))

                # Show a message box when the download is complete
                messagebox.showinfo("Download Complete", "The result has been downloaded successfully.")

                # Delete the file
                base_dir = os.path.dirname(os.path.abspath(__file__))
                print('Base_dir:', base_dir)

                # Disable the download button
                app.download_button.config(state="disabled")

            except Exception as e:
                pass
                # Show error message in a label
                error_label.config(text=str(e))
                logging.error(str(e))

        # Create a button to download the result
        self.download_button = tk.Button(self, text="Download", font=("Arial", 12, "bold"), fg="#FFFFFF",
                                         bg="#4B8BBE", command=download_result)
        self.download_button.config(state="disabled")  # Disable the download button by default
        self.download_button.pack(pady=10)

        # Create a label for error messages
        error_label = tk.Label(self, text="", font=("Arial", 12), fg="red", bg="#E0E0E0")
        error_label.pack(pady=10)
    # def create_widgets(self):
    #     # Create a label for the title
    #     title_label = tk.Label(self, text="Rami - Excel", font=("Arial", 24, "bold"), fg="#FFFFFF", bg="#4B8BBE")
    #     title_label.pack(pady=20)
    #
    #     # Create a frame for the input and buttons
    #     frame = tk.Frame(self, bg="#E0E0E0")
    #     frame.pack(padx=20, pady=10)
    #
    #     # Create a label for the input field
    #     input_label = tk.Label(frame, text="Input:", font=("Arial", 12), fg="#000000", bg="#E0E0E0")
    #     input_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
    #
    #     # Create an entry field for the user input
    #     self.input_var = tk.StringVar()
    #     self.input_var.set("Kindly enter your URL")
    #
    #     self.input_entry = tk.Entry(frame, font=("Arial", 12), width=30, textvariable=self.input_var)
    #     self.input_entry.grid(row=0, column=1, padx=5, pady=5)
    #
    #     # Clear the placeholder text when the input field is clicked
    #     def clear_placeholder(event):
    #         current_text = self.input_entry.get()
    #         if current_text == "Kindly enter your URL":
    #             self.input_var.set("")
    #             self.input_entry.unbind("<FocusIn>")  # Unbind the event after clearing the text
    #
    #     self.input_entry.bind("<FocusIn>", clear_placeholder)
    #
    #     # Bind the Enter key press event to the Run button click
    #     self.input_entry.bind("<Return>", lambda event: run_button.invoke())
    #
    #     # Bind the Ctrl + x, Ctrl + c, and Ctrl + v key combinations
    #     self.input_entry.bind("<KeyRelease>", _onKeyRelease)
    #
    #     # Set the focus to the input field when the UI is opened
    #     self.input_entry.focus_set()
    #
    # # Function to handle key release events
    #     def _onKeyRelease(event):
    #         ctrl = (event.state & 0x4) != 0
    #
    #         if event.keycode == 88 and ctrl and event.keysym.lower() != "x":
    #             event.widget.event_generate("<<Cut>>")
    #
    #         if event.keycode == 86 and ctrl and event.keysym.lower() != "v":
    #             event.widget.event_generate("<<Paste>>")
    #
    #         if event.keycode == 67 and ctrl and event.keysym.lower() != "c":
    #             event.widget.event_generate("<<Copy>>")
    #
    #     def run_spider():
    #         input_value = self.input_entry.get()
    #
    #         if not input_value:
    #             # Show a message box when the input is empty
    #             messagebox.showwarning("Empty Input", "Kindly enter the URL.")
    #             return
    #
    #         try:
    #             AppslandSpider(input_value)
    #
    #             # Show a message box when the spider completes
    #             messagebox.showinfo("Scraping Completed", "The spider has finished running.")
    #             self.download_button.config(state="normal")  # Enable the download button
    #
    #         except Exception as e:
    #             # Show error message in a label
    #             error_label.config(text=str(e))
    #             logging.error(str(e))
    #
    #     # Create a button to run the spider
    #     run_button = tk.Button(frame, text="Run", font=("Arial", 12, "bold"), fg="#FFFFFF", bg="#4B8BBE",
    #                            command=run_spider)
    #     run_button.grid(row=0, column=2, padx=5, pady=5)
    #
    #     def download_result():
    #         try:
    #             # Get the file path to save the result
    #             default_filename = "AppsLandTenderPremises.xlsx"  # Default filename with extension
    #             file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=default_filename)
    #             base_dir = os.path.dirname(os.path.abspath(__file__))
    #             print('Base directory:', base_dir)
    #
    #             # Copy the desired file to the specified location
    #             shutil.copy("output/AppsLandTenderPremises.xlsx", file_path)
    #             print('shutil.copy:', shutil.copy("output/AppsLandTenderPremises.xlsx", file_path))
    #
    #             # Show a message box when the download is complete
    #             messagebox.showinfo("Download Complete", "The result has been downloaded successfully.")
    #
    #             # Delete the file
    #             base_dir = os.path.dirname(os.path.abspath(__file__))
    #             print('Base_dir:', base_dir)
    #
    #             # Disable the download button
    #             app.download_button.config(state="disabled")
    #
    #         except Exception as e:
    #             pass
    #             # Show error message in a label
    #             error_label.config(text=str(e))
    #             logging.error(str(e))
    #
    #         # Disable the download button by default
    #         self.download_button.config(state="disabled")
    #         self.download_button.pack(pady=10)
    #     # Create a button to download the result
    #     self.download_button = tk.Button(self, text="Download", font=("Arial", 12, "bold"), fg="#FFFFFF",
    #                                      bg="#4B8BBE", command=download_result)
    #     self.download_button.config(state="disabled")  # Disable the download button by default
    #     self.download_button.pack(pady=10)
    #
    #     # Create a label for error messages
    #     error_label = tk.Label(self, text="", font=("Arial", 12), fg="red", bg="#E0E0E0")
    #     error_label.pack(pady=10)
    #

if __name__ == "__main__":
    configure_logging(install_root_handler=False)
    logging.basicConfig(
        filename=f'logs.txt',
        format='%(levelname)s: %(message)s',
        level=logging.INFO,
        filemode='w'
    )
    app = SpiderGUI()
    app.mainloop()
