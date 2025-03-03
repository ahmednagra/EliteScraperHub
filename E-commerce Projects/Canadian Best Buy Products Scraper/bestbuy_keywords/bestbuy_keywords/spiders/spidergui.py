import tkinter as tk
from tkinter import messagebox
from tkinter import filedialog

from scrapy.crawler import CrawlerProcess

from individuals_pages import SitemapsSpider


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

        def run_spider():
            input_value = self.input_entry.get()
            urls = [input_value]

            try:
                # Create a CrawlerProcess
                process = CrawlerProcess()

                # Start the spider
                process.crawl(SitemapsSpider,  urls=urls)
                process.start()

                # Show a message box when the spider completes
                messagebox.showinfo("Spider Completed", "The spider has finished running.")
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
                file_path = filedialog.asksaveasfilename(defaultextension=".txt")

                # Save the result to the file
                # ...

                # Show a message box when the download is complete
                messagebox.showinfo("Download Complete", "The result has been downloaded successfully.")
            except Exception as e:
                # Show error message in a label
                error_label.config(text=str(e))

        # Create a button to download the result
        download_button = tk.Button(self, text="Download Result", font=("Arial", 12, "bold"), fg="#FFFFFF",
                                    bg="#4B8BBE", command=download_result)
        download_button.pack(pady=10)

        # Create a label for error messages
        error_label = tk.Label(self, text="", font=("Arial", 12), fg="red", bg="#E0E0E0")
        error_label.pack(pady=10)


if __name__ == "__main__":
    app = SpiderGUI()
    app.mainloop()
