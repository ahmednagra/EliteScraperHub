# import os
# from urllib.parse import urlparse
# import requests
# from microsoftgraph.client import Client
#
# # Define your application ID (client ID), client secret, and tenant ID
# client_id = '6cde4b83-a874-4111-915b-7d17f33a7323'
# client_secret_value = '3d48Q~gguW~3Z6MMSfkgNPQZTKifbHmKDgpJlb9x'
# client_secret = 'bda1ac8a-6ec4-4a04-b7b6-a9d7dceca855'
# tenant_id = 'f8cdef31-a31e-4b4a-93e4-5f571e91255a'
# scope = ['Files.Read.All']
#
# # Define the file link to download from OneDrive
# file_link = "https://1drv.ms/x/s!AtGtj5YOPVIhbKzER0bDXyofBk4?e=2AbhWU"
#
# def get_access_token():
#     # Define the token URL
#     token_url = f'https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token'
#
#     # Define the data for token request
#     token_data = {
#         'grant_type': 'client_credentials',
#         'client_id': client_id,
#         'client_secret': client_secret_value,
#         'scope': 'https://graph.microsoft.com/.default'
#     }
#
#     # Obtain an access token
#     response = requests.post(token_url, data=token_data)
#     access_token = response.json()['access_token']
#
#     return access_token
#
#
# def get_drive_info(access_token):
#     # Define the headers with the access token
#     headers = {
#         'Authorization': 'Bearer ' + access_token,
#         'Content-Type': 'application/json'
#     }
#
#     # Define the Microsoft Graph API endpoint to get information about the root drive
#     api_url = 'https://graph.microsoft.com/v1.0/drive/root'
#
#     # Make a GET request to retrieve information about the root drive
#     response = requests.get(api_url, headers=headers)
#
#     # Check the response status code and content
#     if response.status_code == 200:
#         drive_info = response.json()
#         return drive_info
#     else:
#         print("Failed to retrieve drive information:", response.text)
#         return None
#
#
# # Function to download the file from OneDrive
# def download_file(file_link):
#     # Extract the file name from the URL
#     parsed_url = urlparse(file_link)
#     file_name = os.path.basename(parsed_url.path)
#
#     response = requests.get(file_link)
#     if response.status_code == 200:
#         with open(file_name, 'wb') as f:
#             f.write(response.content)
#         print("File downloaded successfully")
#     else:
#         print("Failed to download file")
#
#
# if __name__ == "__main__":
#     client = Client(client_id, client_secret, account_type='common')
#     a=1
#     access_token = get_access_token()
#     drive_info = get_drive_info(access_token)
#
#     # Download the file from OneDrive
#     download_file(file_link)
import msal
from msal import PublicClientApplication, ConfidentialClientApplication  # Depending on your scenario
import requests

# Azure AD app details (replace with yours)
CLIENT_ID = '6cde4b83-a874-4111-915b-7d17f33a7323'
CLIENT_SECRET = 'bda1ac8a-6ec4-4a04-b7b6-a9d7dceca855'
AUTHORITY = 'https://login.microsoftonline.com/common'  # v2.0 endpoint
SCOPES = ["https://graph.microsoft.com/Files.ReadWrite.All"]
REDIRECT_URI = "http://localhost:8080/"  # Placeholder, not used in this script

def get_access_token(use_confidential_flow=False):
    """
    Acquires an access token using user consent flow or confidential client flow.
    """
    if use_confidential_flow:
        app = ConfidentialClientApplication(client_id=CLIENT_ID, authority=AUTHORITY, client_secret=CLIENT_SECRET)
        return app.acquire_token_for_client(scopes=SCOPES)
    else:
        app = PublicClientApplication(CLIENT_ID, authority=AUTHORITY)
        # Use acquire_token_interactive for user consent flow
        flow = app.initiate_device_flow(scopes=SCOPES)
        print(flow['message'])  # Print the user code and verification URL
        return app.acquire_token_by_device_flow(flow)

def download_file_from_onedrive(file_id, download_path):
    access_token = get_access_token()
    headers = {"Authorization": f"Bearer {access_token.pop('access_token')}"}
    download_url = f"https://graph.microsoft.com/v1.0/me/drive/items/{file_id}/download"

    response = requests.get(download_url, headers=headers, stream=True)

    if response.status_code == 200:
        with open(download_path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        print(f"File downloaded successfully: {download_path}")
    else:
        print(f"Error downloading file: {response.status_code}")

if __name__ == "__main__":
    app = msal.ConfidentialClientApplication(
        config["client_id"], authority=config["authority"],
        client_credential=config["secret"],
    )
    # Choose between confidential or public client flow based on your scenario
    access_token = get_access_token(use_confidential_flow=False)  # User consent flow (default)
    # access_token = get_access_token(use_confidential_flow=True)  # Confidential flow (optional)


