#!/bin/bash

# Check if Python is installed
if ! command -v python3 &> /dev/null
then
    echo "Python is not installed. Please install Python from https://www.python.org/downloads/"
    exit 1
fi

# Create a virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating a virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment
echo "Activating the virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Prompt user for spider selection
echo "Select the spider(s) to run:"
echo "1 - Psychology Today"
read -p "Enter spider numbers (e.g. 1 2 3 for multiple spiders, or 0 for all): " spiders

# Run selected spiders
if [[ "$spiders" == "0" ]]; then
    echo "Running all spiders..."
    echo "Scraper 'Psychology Today' is currently running..."
    scrapy crawl Psychology
else
    for spider in $spiders; do
        if [[ "$spider" == "1" ]]; then
            echo "Scraper 'Psychology Today' is currently running..."
            scrapy crawl Psychology
        fi
    done
fi

# Keep terminal open
read -p "All selected spiders have completed. Press any key to exit..."
