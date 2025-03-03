import scrapy
import re
import textwrap
import os
# from bs4 import BeautifulSoup
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, letter
from markdownify import markdownify

class IrishSpiderSpider(scrapy.Spider):
    name = "irish_spider"

    def __init__(self, *args, **kwargs):
        super(IrishSpiderSpider, self).__init__(*args, **kwargs)

        # List of folder names to check and create
        folders = [
            "TaxesConsolidationAct1997",
            "Value-AddedTaxConsolidationAct2010",
            "StampDutiesConsolidationAct1999",
            "CapitalAcquisitionsTaxConsolidationAct2003",
            "CompaniesAct2014"
        ]

        # Get the current working directory (main directory)
        main_directory = os.getcwd()
        # output_folder = os.makedirs('logs', exist_ok=True)
        output_folder = os.path.join(main_directory, 'output')
        self.irisbook_folder = os.path.join(output_folder, 'irishstatutebook')
        if not os.path.exists(self.irisbook_folder):
            os.makedirs(self.irisbook_folder)

        # Iterate through the list of folder names
        for folder_name in folders:
            # Construct the full path for each folder
            folder_path = os.path.join(self.irisbook_folder, folder_name)

            # Check if the folder exists; if not, create it
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)
                self.log(f"Folder '{folder_name}' created in the main directory.")
            else:
                self.log(f"Folder '{folder_name}' already exists in the main directory.")

    def start_requests(self):
        urls = ['https://www.irishstatutebook.ie/eli/1997/act/39/section/1/enacted/en/html#part1',
                'https://www.irishstatutebook.ie/eli/2010/act/31/section/1/enacted/en/html#part1',# vat2010
                'https://www.irishstatutebook.ie/eli/1999/act/31/section/1/enacted/en/html#part1', #sdca1999
                'https://www.irishstatutebook.ie/eli/2003/act/1/section/1/enacted/en/html#part1',#cat2003
                'https://www.irishstatutebook.ie/eli/2014/act/38/section/1/enacted/en/html#part1'#cat2014
        ]
        for index, url in enumerate(urls):
            folder_name = ''
            abbr = ''
            if index == 0:
                folder_name = 'TaxesConsolidationAct1997'
                abbr = 'tca'
            elif index == 1:
                folder_name = 'Value-AddedTaxConsolidationAct2010'
                abbr = 'vat'
            elif index == 2:
                folder_name = 'StampDutiesConsolidationAct1999'
                abbr = 'sdca'
            elif index == 3:
                folder_name = 'CapitalAcquisitionsTaxConsolidationAct2003'
                abbr = 'cat'
            elif index == 4:
                folder_name = 'CompaniesAct2014'
                abbr = 'cat'
            yield scrapy.Request(url, callback=self.parse, meta={'folder_name': folder_name, 'abbr': abbr})

    def parse(self, response, **kwargs):
        # Extract the content of the act
        folder_name = response.meta.get('folder_name')
        abbr = response.meta.get('abbr')
        act = response.css('#act').get()
        act = markdownify(act)

        text = act.replace('|', '').replace('*', '').replace("\\", "").replace(' ___ ', '/').replace('---', '').replace('\n', '\n\n').replace('[', '').replace(']', '').strip()
        # Regular expression to match links in parentheses containing ".html"
        pattern = r'\([^)]*\.html[^)]*\)'

        # Replace matched patterns with an empty string
        text = re.sub(pattern, '', text)
        schehule_number_pattern = r"SCHEDULE\s(\d+)"
        # schehule_title_pattern = r"SCHEDULE\s\d+\s(.*)"


        schehule_number = self.extract_field(schehule_number_pattern, text, "Schehule Number")
        # schehule_title = self.extract_field(schehule_title_pattern, text, "Schehule Title")
        section_no = response.css('a+ p b::text').get()
        if section_no is None:
            section_no = response.css('b::text').get()
        if section_no:
            section_no = section_no.replace('.', '')
        title = response.css('.content-title::text').get().strip()
        year_pattern = r"\b\d{4}\b"
        match = re.search(year_pattern, title)
        year = '-'
        if match:
            year = match.group(0)
        # Determine json_name
        if schehule_number:
            json_name = f"schedule{schehule_number}_{abbr}{year}"
        else:
            json_name = f"s{section_no}_{abbr}{year}"


        # Save to JSON file
        try:
            # file_name = f"{folder_name}/{json_name}.pdf"
            # Construct the full path for the file inside the corresponding folder
            file_path = os.path.join(self.irisbook_folder, folder_name, f"{json_name}.pdf")

            # Ensure the folder exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            # Create a wider PDF page with landscape orientation
            page_width, page_height = landscape(letter)  # Landscape for wider page
            c = canvas.Canvas(file_path, pagesize=(page_width, page_height))

            # Set smaller font and margins
            c.setFont("Helvetica", 10)  # Smaller font size
            margin = 40  # Reduce margins for more content space
            line_spacing = 12  # Line spacing
            max_width = page_width - 2 * margin  # Adjust width for text wrapping

            # Handle multi-line text with wrapping
            y_position = page_height - margin  # Start height for the text
            for line in text.splitlines():
                if not line.strip():  # Check for blank lines
                    y_position -= line_spacing  # Add spacing for blank lines
                    continue
                # Adjust wrapping width based on font size and max_width
                wrapped_lines = textwrap.wrap(line, width=int(max_width / 6.5))
                for wrapped_line in wrapped_lines:
                    if y_position < margin:  # Check if there is space left on the page
                        c.showPage()  # Start a new page
                        c.setFont("Helvetica", 10)  # Reset font after page break
                        y_position = page_height - margin  # Reset starting height
                    c.drawString(margin, y_position, wrapped_line)
                    y_position -= line_spacing

            # Save the PDF
            c.save()

            print(f"PDF saved as {file_path}")
        except Exception as e:
            print(f"Error saving file: {e}")

        next = response.css('.navigation-toolbar li:nth-child(2) a::attr(href)').get()
        if next:
            next_page = response.urljoin(next)
            yield scrapy.Request(next_page, callback=self.parse, meta={'folder_name': folder_name, 'abbr': abbr})

    # Safe extraction function
    def extract_field(self, pattern, text, field_name):
        match = re.search(pattern, text)
        if match:
            return match.group(1)
        else:
            return None

    def extract_formula(self, td):
        try:
            # Extract the left part (G × S ×)
            left_td = td.find('td', valign="middle")
            left_part = left_td.find('p').get_text(strip=True) if left_td else ""

            # Extract the right part (H___J)
            right_td = td.find('td', valign="top")
            if right_td:
                right_parts = [p.get_text(strip=True) for p in right_td.find_all('p')]
                right_formula = "".join(right_parts)
            else:
                right_formula = ""

            # Combine parts to form the formula
            formula = f"{left_part}({right_formula})"
            return formula
        except Exception as e:
            # Log or print the error for debugging
            self.logger.error(f"Error extracting formula: {e}")
            return None

