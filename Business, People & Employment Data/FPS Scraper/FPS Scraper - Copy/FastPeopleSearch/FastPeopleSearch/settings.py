# Scrapy settings for FastPeopleSearch project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

BOT_NAME = 'FastPeopleSearch'

SPIDER_MODULES = ['FastPeopleSearch.spiders']
NEWSPIDER_MODULE = 'FastPeopleSearch.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
# USER_AGENT = 'FastPeopleSearch (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
# CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
# DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
# CONCURRENT_REQUESTS_PER_DOMAIN = 16
# CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
# COOKIES_ENABLED = False

# Disable Telnet Console (enabled by default)
# TELNETCONSOLE_ENABLED = False

# Override the default request headers:
# DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
# }

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
# SPIDER_MIDDLEWARES = {
#    'FastPeopleSearch.middlewares.FastpeoplesearchSpiderMiddleware': 543,
# }

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
# DOWNLOADER_MIDDLEWARES = {
#    'FastPeopleSearch.middlewares.FastpeoplesearchDownloaderMiddleware': 543,
# }

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
# EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
# }

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
# ITEM_PIPELINES = {
#    'FastPeopleSearch.pipelines.FastpeoplesearchPipeline': 300,
# }

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
# AUTOTHROTTLE_ENABLED = True
# The initial download delay
# AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
# AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
# AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
# AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
# HTTPCACHE_ENABLED = True
# HTTPCACHE_EXPIRATION_SECS = 0
# HTTPCACHE_DIR = 'httpcache'
# HTTPCACHE_IGNORE_HTTP_CODES = []
# HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
# Number of retries for failed requests
# RETRY_ENABLED = True
# RETRY_TIMES = 5  # Increase if necessary
#
# # Delay between retries to prevent spamming the server
# RETRY_BACKOFF_BASE = 2  # In seconds; backoff between retries

# ZYTE_API_KEY = "ee13c722f64e47a1955faf2e864e63f8"  # TODO Add key here
# #
# # # ADDONS = {
# # #     "scrapy_zyte_api.Addon": 500,
# # # }
#
# ZYTE_API_TRANSPARENT_MODE = True
#
# DOWNLOAD_HANDLERS = {
#     "http": "scrapy_zyte_api.ScrapyZyteAPIDownloadHandler",
#     "https": "scrapy_zyte_api.ScrapyZyteAPIDownloadHandler",
# }
# DOWNLOADER_MIDDLEWARES = {
#     "scrapy_zyte_api.ScrapyZyteAPIDownloaderMiddleware": 1000,
# }
# REQUEST_FINGERPRINTER_CLASS = "scrapy_zyte_api.ScrapyZyteAPIRequestFingerprinter"
#
# Enable Zyte Smart Proxy
# ZYTE_SMARTPROXY_ENABLED = True
#
# # Your Zyte Proxy API key
# ZYTE_SMARTPROXY_APIKEY = 'ee13c722f64e47a1955faf2e864e63f8'
#
# # Set the desired location, e.g., "US" for USA
# ZYTE_SMARTPROXY_COUNTRY = "US"
#
# ADDONS = {
#     "scrapy_zyte_api.Addon": 500,
# }
# ZYTE_API_KEY = "ee13c722f64e47a1955faf2e864e63f8"