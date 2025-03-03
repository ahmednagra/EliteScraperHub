# TruePeopleSearch Scrapy Project

## Overview
This project is a Scrapy-based web scraper designed to extract information from **True People Search**. The scraper reads addresses and zip codes from an Excel file, formats them, and sends requests to the True People Search website to retrieve detailed data of first 5 Persons.

The extracted data is saved into a timestamped CSV file located in the `output` folder.

---

## Features
- **Excel File Input:** Reads input data from `.xlsx` files in the `input` folder.
- **Dynamic URL Generation:** Formats addresses and zip codes to create search queries.
- **Data Extraction:** Scrapes data and outputs it to a CSV file.
- **Folder Management:** Automatically manages input and output directories.
- **Timestamped Output:** Creates unique CSV files with timestamps to avoid overwrites.

---


## Prerequisites

1. Python 3.8 or above
2. Required Python packages:
   - Scrapy
   - Pandas
   - OpenPyXL (for reading `.xlsx` files)
3. ### .env File Instructions  

- The project includes a `.env` file located in the root directory.  

- Open the `.env` file and paste the latest and updated Zyte API key in the following format:  
   ```dotenv  
   ZYTE_API_KEY=your_updated_zyte_api_key_here  
   ```  

- Replace `your_updated_zyte_api_key_here` with your current Zyte API key.  

The scraper will automatically use this API key for authentication during execution.




## How to Use

1. **Prepare Input Data:**
   - Place an Excel file containing `Owner Mailing Address` and `Owner Mailing Zip` columns into the `input` folder.

2. **Run the Spider:**
   - To run the spider just Double-click the `run_spider.bat` file it well the install all dependencies automatically in 
    a virtual environment 
     

3. **View Results:**
   - Check the `output` folder for the generated CSV file. Each file is timestamped for uniqueness.



Output File Naming
The output CSV file's name includes a timestamp for uniqueness. To customize it, modify the `csv_file` variable in the `start_requests` method.

---

## Error Handling
- If no Excel file is found in the `input` folder, the spider will log a message and terminate.
- The script ensures that the `output` folder exists before attempting to save data.
