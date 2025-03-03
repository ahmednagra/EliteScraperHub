import csv
import glob
from datetime import datetime
from urllib.parse import urljoin
from collections import OrderedDict
from scrapy import Spider, Request, signals


def get_scrapeops_settings_from_file():
    with open('input/scrapeops_proxy_settings.txt', mode='r', encoding='utf-8') as input_file:
        data = {}

        for row in input_file.readlines():
            if not row.strip():
                continue

            try:
                key, value = row.strip().split('==')
                data.setdefault(key.strip(), value.strip())
            except ValueError:
                pass

        api_key = data.get('api_key', '')
        max_concurrency = data.get('max_concurrency_allowed', '')
        concurrent_requests = int(max_concurrency) - 1 if max_concurrency.isdigit() and int(max_concurrency) > 1 else 1

        return api_key, concurrent_requests


class FBRefSpider(Spider):
    name = "fbref"
    base_url = "https://fbref.com"
    scrapeops_apikey, scrapeops_concurrency = get_scrapeops_settings_from_file()

    custom_settings = {
        'CONCURRENT_REQUESTS': scrapeops_concurrency,

        'SCRAPEOPS_API_KEY': scrapeops_apikey,
        'SCRAPEOPS_PROXY_ENABLED': True if scrapeops_apikey else False,
        'DOWNLOADER_MIDDLEWARES': {
            'scrapeops_scrapy_proxy_sdk.scrapeops_scrapy_proxy_sdk.ScrapeOpsScrapyProxySdk': 725,
        },

    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.season_urls = self.get_season_urls_from_csv()
        self.current_items_scraped = 0
        self.current_items_scrape_list = []
        self.filename = f'output/FBref Matches {datetime.now().strftime("%d%m%Y%H%M%S")}.csv'
        self.fields = ["Number", "Country", "Comp", "Season", "Round", "Wk", "Day", "Date", "Time", "Home", "xG_h", "Score",
                       "xG_a", "Away", "Attendance", "Venue", "Referee", "href", "CoachH", "CoachA", "CaptainH",
                       "CaptainA", "url_CaptainH", "url_CaptainA", "goal1", "goal2", "goal3", "goal4", "goal5",
                       "goal6", "goal7", "goal8", "goal9", "goal10", "goal11", "goal12", "goal13", "goal14",
                       "goal15", "goal16", "goal17", "goal18", "goal19", "goal20", "goal21", "goal22", "goal23",
                       "goal24", "goal25"]
        self.mode = 'w'

    def parse(self, response, **kwargs):
        try:
            # Extract competition name and season from the page
            comp = response.css('#sched_all_sh h2 span::text, #all_sched h2 span::text').re_first(r'\d.*?(\D+)$')
            comp = comp.strip() if comp else ''
            season = response.css('#meta h1::text').re_first(r'(\d+)')
            season = season.strip() if season else ''

            country = ''

            # Get modified headers
            headers = self.get_modify_headers(response)

            # Find index of 'Score' header
            score_index = headers.index('score')
            if not score_index:
                self.logger.error(f'No Headers found in the Url :{response.url}')
                return

            # Iterate over table rows, skip first row for Headers
            for index, row in enumerate(response.css('table tr')[1:], start=1):
                cells = row.css('th, td')
                row_data = self.get_row_data(row)

                if len(cells) > score_index:  # Check if the cell exists
                    url = urljoin(self.base_url, row.css('[data-stat="match_report"] a::attr(href)').get(''))
                    if url == 'https://fbref.com':
                        continue

                    item = {
                        'comp': comp,
                        'season': season,
                        'country': country,
                        'match_report_url': url,
                        'row_data': row_data
                    }

                    response.meta['item'] = item
                    yield Request(url=url, callback=self.parse_match, meta=response.meta)
        except Exception as e:
            self.logger.error(f'Error Parse Function Error :{e} URL: {response.url}')

    def parse_match(self, response):
        try:
            # Extracting home team information
            teamH = response.css('.scorebox > div')
            coach_h = teamH.css('.datapoint:contains("Manager")::text').get('').replace(':', '').strip()
            captain_h = teamH.css('.datapoint:contains("Captain") a::text').get('')
            url_h = teamH.css('.datapoint:contains("Captain") a::attr(href)').get('')
            url_captain_h = urljoin(self.base_url, url_h) if url_h else ''
            team_h_goals = self.get_team_goals(key='H', selector=response.css('.scorebox #a >div'))

            # Extracting away team information
            team_a = response.css('.scorebox > div:nth-child(2), div#b')
            coach_a = team_a.css('.datapoint:contains("Manager")::text').get('').replace(':', '').strip()
            captain_a = team_a.css('.datapoint:contains("Captain") a::text').get('')
            url_a = team_a.css('.datapoint:contains("Captain") a::attr(href)').get('')
            url_captain_a = urljoin(self.base_url, url_a) if url_a else ''
            team_a_goals = self.get_team_goals(key='A', selector=response.css('.scorebox #b >div'))

            # Combine home and away team goals into a single list
            all_goals = team_h_goals + team_a_goals

            match_details = response.meta.get('item', {})

            item = OrderedDict()
            item['Number'] = response.meta.get('index_no', 0)
            item['Country'] = match_details.get('country', '')
            item['Comp'] = match_details.get('comp', '')
            item['Season'] = match_details.get('season', '')
            item['Round'] = match_details.get('row_data', {}).get('round', '')
            item['Wk'] = match_details.get('row_data', {}).get('gameweek', '')
            item['Day'] = match_details.get('row_data', {}).get('dayofweek', '')
            item['Date'] = match_details.get('row_data', {}).get('date', '')
            item['Time'] = match_details.get('row_data', {}).get('start_time', '')
            item['Home'] = match_details.get('row_data', {}).get('home_team', '')
            item['xG_h'] = match_details.get('row_data', {}).get('home_xg', '')
            item['Score'] = match_details.get('row_data', {}).get('score', '')
            item['xG_a'] = match_details.get('row_data', {}).get('away_xg', '')
            item['Away'] = match_details.get('row_data', {}).get('away_team', '')
            item['Attendance'] = match_details.get('row_data', {}).get('attendance', '')
            item['Venue'] = match_details.get('row_data', {}).get('venue', '')
            item['Referee'] = match_details.get('row_data', {}).get('referee', '')
            item['href'] = match_details.get('match_report_url', '') or match_details.get('row_data', {}).get(
                'match_report', '')
            item['CoachH'] = coach_h
            item['CoachA'] = coach_a
            item['CaptainH'] = captain_h
            item['CaptainA'] = captain_a
            item['url_CaptainH'] = url_captain_h
            item['url_CaptainA'] = url_captain_a

            for i, goal in enumerate(all_goals):
                item[f"goal{i + 1}"] = goal if i < len(all_goals) else ""

            self.current_items_scraped += 1
            print('Current Scrapped Items :', self.current_items_scraped)

            self.current_items_scrape_list.append(item)

        except Exception as e:
            self.logger.error(f'Error parse Match Detail Error :{e} URL:{response.url}')

    def get_season_urls_from_csv(self):
        """
        Read input data from a CSV file and return it as a list of dictionaries.

        Returns:
        list: A list of dictionaries containing the data read from the CSV file.
              Each dictionary represents a row, where the keys are the column headers
              and the values are the corresponding row values, along with an 'index'
              key indicating the row number.
              Returns an empty list if the file is empty or cannot be read.
        """
        try:
            csv_filename = glob.glob('input/*.csv')[0]  # Read first CSV file from the input folder.
        except IndexError:
            print('No CSV file found in input folder for Season URLs')
            return []

        data = []

        try:
            with open(csv_filename, mode='r', encoding='utf-8') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                for index, row in enumerate(csv_reader, start=1):
                    row['index'] = index  # Add index to each row
                    data.append(row)

            return data
        except Exception as e:
            error = f"An error occurred while reading the file '{csv_filename}': {e}"
            print(error)
            self.logger.error(error)
        return []

    def get_row_data(self, row):
        try:
            data = {}
            th_tags = row.css('th')

            for th in th_tags:
                header = th.css('::attr(data-stat)').get('').strip()
                value = th.css('::text').get('').strip()
                data[header] = value

            # Extract data from <td> elements
            td_tags = row.css('td')

            for td in td_tags:
                header = td.css('::attr(data-stat)').get('').strip()
                value = td.css('a::text').get('').strip() or td.css('::text').get('').strip()
                if 'match_report' in header:
                    url = td.css('a::attr(href)').get('').strip()
                    value = urljoin(self.base_url, url) if url else ''
                data[header] = value

            return data
        except Exception as e:
            print(f"Error occurred while extracting row data: {e}")
            return {}

    def get_modify_headers(self, response):
        headers = [header.strip().lower() for header in
                   response.css('#sched_all thead tr th::text, #all_sched thead tr th::text').getall()]

        # Modify headers to handle multiple 'xG' columns
        xg_count = 0
        for i, header in enumerate(headers):
            if header == 'xg':
                xg_count += 1
                if xg_count == 1:
                    headers[i] = 'xg_h'
                elif xg_count == 2:
                    headers[i] = 'xg_a'

        return headers

    def get_team_goals(self, key, selector):
        goals = []
        try:
            for goal in selector:
                if goal.css('.yellow_red_card').get(''):
                    continue

                player_name = goal.css('a::text').get('').strip()
                player_link = goal.css('a::attr(href)').get('')
                playerH_link = urljoin(self.base_url, player_link) if player_link else ''
                time = goal.css('div::text').re_first(r'\b(\d+)\b')

                goals.append(f"{key}_{time}_{player_name}_{playerH_link}")
        except Exception as e:
            self.logger.error(f"Error extracting {key} team goals: {e}")

        return goals

    def write_items_to_csv(self):
        with open(self.filename, mode=self.mode, newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fields)
            if self.mode == 'w':
                writer.writeheader()
            for record in self.current_items_scrape_list:
                row = {field: record.get(field, '') for field in self.fields}
                writer.writerow(row)

        self.mode = 'a'

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(FBRefSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_idle, signal=signals.spider_idle)
        return spider

    def spider_idle(self):
        """
        Handle spider idle state by crawling next brand if available.
        """
        if self.current_items_scrape_list:
            self.write_items_to_csv()
            self.current_items_scrape_list = []

        if self.season_urls:
            season = self.season_urls.pop(0)
            season_url = season.get('Season URL', '')
            index_no = season.get('index', 0)
            self.crawler.engine.crawl(Request(url=season_url,
                                              callback=self.parse, dont_filter=True,
                                              meta={'handle_httpstatus_all': True, 'index_no': index_no}))
