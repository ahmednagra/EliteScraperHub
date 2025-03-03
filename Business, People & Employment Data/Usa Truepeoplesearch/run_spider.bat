@echo off
REM Navigate to the project directory
cd truepeoplesearch

REM Create a virtual environment in the 'venv' folder
python -m venv venv

REM Activate the virtual environment
call venv\Scripts\activate

REM
pip install scrapy
pip install scrapy_zyte_api
pip install scrapy_poet
pip install python-dotenv
pip install pandas
pip install openpyxl

REM Run the Scrapy spider
scrapy crawl people_spider

REM Keep the command prompt window open
echo.
echo Press any key to exit...
pause

REM Deactivate the virtual environment
deactivate
