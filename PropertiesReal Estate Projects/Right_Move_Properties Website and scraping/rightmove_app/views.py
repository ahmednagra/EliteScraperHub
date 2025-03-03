import io
import shutil
import zipfile
import pandas as pd
from io import BytesIO
from .right_move import main
from datetime import datetime
import os

from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import HttpResponse, FileResponse
from django.conf import settings


def download_file(request, filename):
    file_path = os.path.join(settings.MEDIA_ROOT, filename)
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)
    else:
        return HttpResponse("File not found", status=404)


class HomePageView(TemplateView):
    """Home page view class"""
    template_name = 'home.html'

    def get(self, request, *args, **kwargs):
        """Handles get requests to '/'"""
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        """Handles POST requests to '/'"""

        current_time = datetime.now().strftime('%d%m%Y_%H%M%S')

        if request.method == 'POST':
            # Get the URLs from the form submission
            urls = request.POST.get('urlInput', '').splitlines()
            # Remove empty strings and duplicates
            urls = list(set(filter(None, urls)))

            errors = []
            all_data = []
            zip_buffer = io.BytesIO()

            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for url in urls:
                    url = url.strip()
                    if not url:
                        continue

                    try:
                        # Call main function to scrape data
                        pdf_content, data, file_name, error_message = main(url)

                        if error_message:
                            errors.append(error_message)
                            continue  # Continue to the next URL

                        if not pdf_content:
                            errors.append(f'Failed to process URL: {url}')
                            continue  # Continue to the next URL

                        # Write PDF file to the zip
                        zipf.writestr(f'{file_name}.pdf', pdf_content)

                        # Append data for Excel file
                        all_data.extend(data)

                    except Exception as e:
                        errors.append(f'Error processing URL {url}: {e}')
                        continue  # Continue to the next URL

                if all_data:
                    # Generate combined Excel file from all data
                    df = pd.DataFrame(all_data)
                    excel_buffer = BytesIO()
                    df.to_excel(excel_buffer, index=False)

                    # Write Excel file to the zip
                    zipf.writestr(f'RightMove Properties {current_time}.xlsx', excel_buffer.getvalue())

            zip_filename = f"RightMove Properties {current_time}.zip"

            # Ensure the MEDIA_ROOT directory exists
            if not os.path.exists(settings.MEDIA_ROOT):
                os.makedirs(settings.MEDIA_ROOT)

            # Remove any existing files in the MEDIA_ROOT directory
            for filename in os.listdir(settings.MEDIA_ROOT):
                file_path = os.path.join(settings.MEDIA_ROOT, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.remove(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    errors.append(f'Failed to delete {file_path}. Reason: {e}')

            # Save the zip file to a temporary location
            zip_path = os.path.join(settings.MEDIA_ROOT, zip_filename)
            with open(zip_path, 'wb') as f:
                f.write(zip_buffer.getvalue())

            # If there are errors, but no PDF or Excel file generated, return only errors
            if errors and not all_data:
                return render(request, self.template_name, {
                    'error_message': ' | '.join(errors),
                    'processing_complete': True  # Flag to indicate processing is complete
                })

            # If there are errors and files generated, return errors with the download link
            if errors:
                return render(request, self.template_name, {
                    'error_message': ' | '.join(errors),
                    'download_url': f"{settings.MEDIA_URL}{zip_filename}",
                    'processing_complete': True  # Flag to indicate processing is complete
                })

            # Return the file response for download
            return FileResponse(open(zip_path, 'rb'), as_attachment=True, filename=zip_filename)

        return render(request, self.template_name)
