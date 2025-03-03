import os
import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog

import shutil
from scrapy.crawler import CrawlerProcess

from appsland import AppslandSpider


class SpiderGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Spider")
        self.configure(bg="#E0E0E0")
        self.create_widgets()

    def create_widgets(self):
        # Create a label for the title
        title_label = tk.Label(self, text="Spider", font=("Arial", 24, "bold"), fg="#FFFFFF", bg="#4B8BBE")
        title_label.pack(pady=20)

        # Create a frame for the input and buttons
        frame = tk.Frame(self, bg="#E0E0E0")
        frame.pack(padx=20, pady=10)

        # Create a label for the input field
        input_label = tk.Label(frame, text="Input:", font=("Arial", 12), fg="#000000", bg="#E0E0E0")
        input_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")

        # Create an entry field for the user input
        self.input_entry = tk.Entry(frame, font=("Arial", 12), width=30)
        self.input_entry.grid(row=0, column=1, padx=5, pady=5)

        # Set focus on the input field by default
        self.input_entry.focus_set()

        # Bind the Enter key press event to the Run button click
        self.input_entry.bind("<Return>", lambda event: run_button.invoke())

        def run_spider():
            input_value = self.input_entry.get()
            urls = [input_value]  # if need pass urls as a list

            if not input_value:
                # Show a message box when the input is empty
                messagebox.showwarning("Empty Input", "Kindly enter the URL.")
                return

            try:
                # Create a CrawlerProcess
                process = CrawlerProcess()
                process.crawl(AppslandSpider, urls=input_value)
                process.start()

                # Show a message box when the spider completes
                messagebox.showinfo("Spider Completed", "The spider has finished running.")
                download_button.config(state="normal")
            except Exception as e:
                # Show error message in a label
                error_label.config(text=str(e))

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
                file_path_to_delete = os.path.join(base_dir, "output", "AppsLandTenderPremises.xlsx")
                os.remove(file_path_to_delete)
                print('File deleted.')

            except Exception as e:
                # Show error message in a label
                error_label.config(text=str(e))

        # Create a button to download the result
        download_button = tk.Button(self, text="Download", font=("Arial", 12, "bold"), fg="#FFFFFF",
                                    bg="#4B8BBE", command=download_result)

        # Check if the result file exists
        result_file_path = "output/AppsLandTenderPremises.xlsx"
        if os.path.exists(result_file_path):
            # Enable the download button if the file exists
            download_button.config(state="normal")
        else:
            # Disable the download button if the file does not exist
            download_button.config(state="disabled")

        download_button.pack(pady=10)

        # Create a label for error messages
        error_label = tk.Label(self, text="", font=("Arial", 12), fg="red", bg="#E0E0E0")
        error_label.pack(pady=10)


if __name__ == "__main__":
    app = SpiderGUI()
    app.mainloop()
