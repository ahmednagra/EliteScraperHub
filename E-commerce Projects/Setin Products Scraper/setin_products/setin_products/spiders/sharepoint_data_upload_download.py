import scrapy
from scrapy.crawler import CrawlerProcess
import openpyxl
import requests
from io import BytesIO


class SharepointExcelSpider(scrapy.Spider):
    name = 'sharepoint_excel_spider'

    # Define settings for Scrapy
    custom_settings = {
        'LOG_LEVEL': 'INFO',
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36'
    }

    def __init__(self):
        super().__init__()
        # SharePoint settings
        self.username = 'nagra.50@hotmail.com'
        self.password = 'Aa$6570684'
        self.excel_file_url = 'https://onedrive.live.com/edit?id=7446C3A5A0C8CBEC!91871&resid=7446C3A5A0C8CBEC!91871&ithint=file%2cxlsx&ct=1714998745430&wdOrigin=OFFICECOM-WEB.START.EDGEWORTH&wdPreviousSessionSrc=HarmonyWeb&wdPreviousSession=26874976-79db-4d62-b265-12f0dd39208b&wdo=2&cid=7446c3a5a0c8cbec'

        self.items_scraped_count = 0
        self.current_scraped_item = []

    def start_requests(self):
        yield scrapy.Request(url=self.excel_file_url, callback=self.parse,
                             meta={'username': self.username, 'password': self.password})

    def parse(self, response, **kwargs):
        a=1
        # Load Excel workbook from response body
        workbook = openpyxl.load_workbook(BytesIO(response.body))
        # Access the active sheet
        sheet = workbook.active
        # Modify Excel data (example: add a new column)
        sheet['A1'].value = 'New Column Header'
        # Save modified Excel workbook to bytes
        modified_excel_bytes = BytesIO()
        workbook.save(modified_excel_bytes)
        modified_excel_bytes.seek(0)
        # Upload modified Excel file to SharePoint
        yield scrapy.Request(url=response.url, method='PUT', body=modified_excel_bytes.getvalue(),
                             headers={
                                 'Content-Type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'},
                             meta=response.meta, callback=self.upload_excel)

    def upload_excel(self, response):
        if response.status == 200:
            print("Excel file uploaded successfully.")
        else:
            print("Failed to upload Excel file.")
