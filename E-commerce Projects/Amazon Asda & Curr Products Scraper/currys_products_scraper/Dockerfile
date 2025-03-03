# Use an official Python runtime as a base image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container
COPY . /app

# Copy input and logs folders to appropriate locations in the container
#COPY input /app/input
COPY currys_products_scraper/input  /app/input

# Expose port (if needed)
EXPOSE 8080

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libffi-dev \
    libssl-dev \
    libxml2 \
    libxslt1-dev \
    zlib1g-dev \
    libjpeg-dev \
    && apt-get clean

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Define environment variable for the spider name (default to 'amazon' if not specified)
ENV SPIDER_NAME=amazon

# Default command to run a specific spider
#CMD ["sh", "-c", "if [ \"$SPIDER_NAME\" == \"all\" ]; then \
#      scrapy crawl amazon && \
#      scrapy crawl asda && \
#      scrapy crawl curry; \
#    else \
#      scrapy crawl $SPIDER_NAME; \
#    fi"]

# Default command to run a specific spider or all spiders
CMD sh -c 'if [ "$SPIDER_NAME" = "all" ]; then \
      scrapy crawl amazon && \
      scrapy crawl asda && \
      scrapy crawl curry; \
    else \
      scrapy crawl "$SPIDER_NAME"; \
    fi'
