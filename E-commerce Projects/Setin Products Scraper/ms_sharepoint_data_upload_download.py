from shareplum import Site, Office365
from shareplum.site import Version
from io import BytesIO
import openpyxl

# SharePoint settings
sharepoint_url = 'https://abc.sharepoint.com/sites/MySharePointSite/'
application_id = 'dd0b99b3-4965-4fea-838a-82c87b6ebc0a'
directory_id = 'f8cdef31-a31e-4b4a-93e4-5f571e91255a'
client_secret = 'e6a5c909-4dd5-4769-bdbe-4200a1887d0b'
excel_file_path = 'https://onedrive.live.com/edit?id=7446C3A5A0C8CBEC!91871&resid=7446C3A5A0C8CBEC!91871&ithint=file%2cxlsx&ct=1714998745430&wdOrigin=OFFICECOM-WEB.START.EDGEWORTH&wdPreviousSessionSrc=HarmonyWeb&wdPreviousSession=26874976-79db-4d62-b265-12f0dd39208b&wdo=2&cid=7446c3a5a0c8cbec'


# Read data from Excel file on SharePoint
def read_excel_from_sharepoint():
    # Connect to SharePoint using client credentials
    authcookie = Office365(sharepoint_url, client_id=application_id, client_secret=client_secret).GetCookies()
    site = Site(sharepoint_url, version=Version.v365, authcookie=authcookie)
    web = site.OpenWeb()

    # Open Excel file
    file = web.GetFileByServerRelativeUrl(excel_file_path)
    data = file.GetContent()

    # Load Excel data into openpyxl workbook
    workbook = openpyxl.load_workbook(BytesIO(data))
    sheet = workbook.active

    # Read data from Excel sheet into a list
    excel_data = []
    for row in sheet.iter_rows(values_only=True):
        excel_data.append(row)

    return excel_data


# Test function
if __name__ == "__main__":
    # Read Excel file from SharePoint
    excel_data = read_excel_from_sharepoint()
    print("Excel Data:")
    print(excel_data[:5])  # Print first 5 rows as a sample
