import logging
import subprocess

from django.core.management.base import BaseCommand, CommandError
from scrapy.crawler import CrawlerProcess

from homes_properties.spiders.homes_rent import HomesRentSpider
from homes_properties.spiders.cyberbackgroundchecks import CyberbackgroundchecksSpider

# from .....

# from scrapy_app.views import full_file_path

# import Spider Class name


class Command(BaseCommand):
    help = 'Scrape data'

    def add_arguments(self, parser):
        parser.add_argument('filepath', type=str, help='Full file path')

    def handle(self, *args, **kwargs):
        full_file_path = kwargs['filepath']
        print('*full_file_path', full_file_path)
        process = CrawlerProcess()
        process.crawl(CyberbackgroundchecksSpider, filepath=full_file_path)  #which spider need to run
        process.start()
