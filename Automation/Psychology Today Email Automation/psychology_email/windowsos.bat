@echo off

REM Check if Python is installed
python --version >nul 2>nul
IF %ERRORLEVEL% NEQ 0 (
    echo Python is not installed. Please install Python from https://www.python.org/downloads/.
    pause
    exit /b
)

REM Create a virtual environment in the 'venv' folder if it doesn't exist
IF NOT EXIST "venv" (
    echo Creating a virtual environment...
    python -m venv venv
)

REM Activate the virtual environment
echo Activating the virtual environment...
call venv\Scripts\activate

REM Install dependencies from requirements.txt
echo Installing dependencies...
pip install -r requirements.txt

title Scrapy Spider Runner

REM Prompt the user for spider selection
echo Select the spider(s) to run:
echo 1 - Psychology Today
set /p spiders="Enter spider numbers (e.g. 1 2 3 for multiple spiders, or 0 for all): "

REM Check if the user wants to run all spiders
IF "%spiders%"=="0" (
    echo Running all spiders...
    echo Scraper 'Psychology Today' is currently running...
    scrapy crawl Psychology

) ELSE (
    REM Loop through the selected spider numbers and run the corresponding spiders in the same CMD window
    FOR %%i IN (%spiders%) DO (
        IF %%i==1 (
            echo Scraper 'Psychology Today' is currently running...
            scrapy crawl Psychology
        )
    )
)

REM Keep the main window open until all spiders finish
echo All selected spiders have completed. Press any key to exit.
pause
