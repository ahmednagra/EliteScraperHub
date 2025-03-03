import os
import json
import subprocess
from django.http import FileResponse
from django.shortcuts import render


def scrape_view(request):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if request.method == 'POST':
        uploaded_file = request.FILES['file']
        print('upload file name 13:', uploaded_file)
        file_path = os.path.join(base_dir, uploaded_file.name)
        print('file_path :', file_path)

        # Save the file to the specified location
        with open(file_path, 'wb') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        try:
            process_args = ["python", "manage.py", "scrape", file_path]
            subprocess.run(process_args)

            with open('filename.csv', 'r') as f:
                filename = json.load(f)
                print('filename from views 78', filename)

            filepath = os.path.join(base_dir, filename)
            print('filepath 81:', filepath)

            with open(filepath, 'rb') as file:
                response = FileResponse(file)
                response['Content-type'] = 'application/octet-stream'
                response['Content-Disposition'] = f'attachment; filename="{filename}"'

            return render(request, 'index.html', {'response': response})

        except subprocess.CalledProcessError as e:
            print(f"Error occurred: {e}")

        except Exception as e:
            print(f"An error occurred: {e}")

    return render(request, 'index.html')


def download_file(request):
    print('welcome download section')
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    print('base dir 102:', base_dir)
    # filename = os.path.join(base_dir,  'sample.csv')
    filename = 'CyberBackgroundChecksRecords.csv'
    print('filename 104:', filename)
    filepath = os.path.join(base_dir, filename)
    print('filepath download_file 106:', filepath)

    response = FileResponse(open(filepath, 'rb'))
    print('resoponse 110:', response)
    response['Content-type'] = 'application/octet-stream'
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response
