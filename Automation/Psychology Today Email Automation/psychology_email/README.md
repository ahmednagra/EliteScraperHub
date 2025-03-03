# Psychology Today Scraper

## Overview

This project is a **Scrapy-Selenium hybrid web scraper** designed to extract therapist profiles from **Psychology Today** and send emails to therapists automatically. Scrapy is responsible for collecting profile URLs efficiently, while Selenium is used separately to handle dynamic content and bypass anti-bot protections for email sending.

## Features

- **Scrapy for Fast Crawling**: Extracts therapist profile URLs efficiently.
- **Selenium for Email Automation**: Handles dynamically loaded pages and form submissions.
- **Blockage Handling**: If Scrapy is blocked, Selenium is used to send emails.
- **Threaded Execution**: Scrapy and Selenium run separately for better performance.
- **Logging & Output**: 
  - `mail_sent.txt`: Stores URLs of profiles where emails were successfully sent.
  - `profiles_urls.txt`: Stores scraped therapist profile URLs.


---

Before running any spider, make sure you have Python installed on your system. Then, follow these steps:


## Prerequisites
- Python 3.x installed on your machine.
- An internet connection to install required dependencies and to extract the data.
Windows OS (for .bat file usage).

1. **Python**
- **Download Python**:  
   Go to the official Python website and download the latest version of Python from the following link:  
   https://www.python.org/downloads

- **Install Python**:  
   During the installation process, **make sure to check the box that says** `Add Python.exe to PATH`. This ensures that Python is accessible from the command line.

- **Verify Installation**:  
   After the installation is complete, open a command prompt or terminal and run the following command to verify the installation:

   ```bash
   python --version
  ```

## Usage

### 1. Run Project to Collect Profile URLs
#### For Mac OS
```sh
.\macos.sh
```

#### Fow Microsoft Windows Operating System

```sh
.\run_spiders.bat
```

### 2. Selenium Automatically Sends Emails
Selenium runs in a separate thread and automatically sends emails while Scrapy is running.

### 3. Stop Execution
Press `CTRL + C` to stop the script. The program logs total profiles and sent emails at the end.

## Notes

- The script uses **incognito mode** in Chrome to minimize tracking.
- The email-sending logic includes checking **checkboxes** submitting forms.
- After **Sending Mail** saved the profile url in sent_mail.txt file
- Make sure to monitor logs for any **blocking issues or errors**.

## License

MIT License

