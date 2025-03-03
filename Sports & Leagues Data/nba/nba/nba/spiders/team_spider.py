import json
import os
import csv
from collections import OrderedDict
from typing import Any

# from scrapy.exceptions import CloseSpider
from scrapy import Spider, Request, signals
from scrapy.http import Response


class NbaTeamSpider(Spider):
    name = 'nba_team'
    base_url = 'https://www.nba.com/'

    team_csv_headers = [ 'TEAM_ID', 'TEAM_NAME',
        'DATE', 'SEASON', 'GAME_TYPE', 'PACE', 'PIE', 'PASSES_MADE', 'SEC_TOUCH',
        'ADJ_REB_CHANCE_%', 'ADJ_OFF_REB_CHANCE_%', 'ADJ_DEF_REB_CHANCE_%',
        'AVG_SPEED_OFF', 'FGM_RA', 'FGA_RA', 'FGM_PAINT', 'FGA_PAINT',
        'FGM_MID-RANGE', 'FGA_MID-RANGE', 'FGM_CORNER', 'FGA_CORNER',
        'FGM_AB', 'FGA_AB', 'DEFLECTIONS', 'SCREEN_AST_PTS', 'DRIVE_PTS',
        'C&S_PTS', 'PULL_UP_PTS', 'PAINT_TOUCH_PTS', 'POST_TOUCH_PTS',
        'ELBOW_TOUCH_PTS'
    ]

    custom_settings = {
        'RETRY_TIMES': 5,
        'RETRY_HTTP_CODES': [500, 502, 503, 504, 400, 403, 404, 408],
        # 'CONCURRENT_REQUESTS': 4,
        # 'DOWNLOAD_DELAY': 1,
    }

    json_headers = {
        'Accept': '*/*',
        'Accept-Language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'Connection': 'keep-alive',
        'Origin': 'https://www.nba.com',
        'Referer': 'https://www.nba.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Google Chrome";v="129", "Not=A?Brand";v="8", "Chromium";v="129"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    def __init__(self):
        super().__init__()
        self.teams_dict = {}
        self.years_range = [
            '2023-24', '2022-23', '2021-22', '2020-21',
            '2019-20', '2018-19', '2017-18', '2016-17', '2015-16'
        ]

    def start_requests(self):
        yield from self.spider_idle

    def parse(self, response: Response, **kwargs: Any) -> Any:
        year = response.meta.get('year')
        season_types = [
            ('Regular Season', 'Regular Season'),
            # ('Playoffs', 'Playoffs'),
            # ('All Star', 'All-Star'),
            # ('PlayIn', 'Play In'),
            # ('IST', 'NBA Cup')
        ]


        # for year in years_range:
            # for season_type in season_types:
        print(f'year : {year}')
        # print(f'Season Type : {season_type[1]}')
        start_year = year.split('-')[0]
        general_advanced_url = (f'https://stats.nba.com/stats/leaguedashteamstats?Conference=&DateFrom=01/01/{start_year}&DateTo=12/31/{start_year}&Division=&GameScope='
                                f'&GameSegment=&Height=&ISTRound=&LastNGames=0&LeagueID=00&Location=&MeasureType=Advanced&Month=0&OpponentTeamID=0&Outcome='
                                f'&PORound=0&PaceAdjust=N&PerMode=Totals&Period=0&PlayerExperience=&PlayerPosition=&PlusMinus=N&Rank=N&Season={year}'
                                f'&SeasonSegment=&SeasonType=Regular Season&ShotClockRange=&StarterBench=&TeamID=0&TwoWay=0&VsConference=&VsDivision=')
        season_type = 'Regular Season'
        yield Request(url=general_advanced_url, callback=self.parse_advance, dont_filter=True,
                      headers=self.json_headers, meta={'year': year, 'season_type': season_type})

    def parse_advance(self, response):
        print('parse_advance\n\n\n')
        year, season_type, start_year, teams_stats = self.get_teams_stats(response)

        print(f'Year :{year} Season Type:{season_type}')
        if len(teams_stats) == 0:
            return

        for team_stat in teams_stats:
            try:
                item = OrderedDict()
                item['TEAM_ID'] = team_stat.get('TEAM_ID', 0)
                item['TEAM_NAME'] = team_stat.get('TEAM_NAME', '')

                item['DATE'] = f'01/01/{start_year}'
                item['SEASON'] = year
                item['GAME_TYPE'] = season_type
                item['PACE'] = team_stat.get('PACE', 0.0)
                item['PIE'] = team_stat.get('PIE', 0.0)

                dict_key = f"{item['SEASON']}_{item['TEAM_ID']}_{item['GAME_TYPE']}"
                # dict_key = f"{item['SEASON']}_{item['ID']}"
                self.teams_dict[dict_key] = item

            except:
                a=1

        tracking_passed_url = (f'https://stats.nba.com/stats/leaguedashptstats?College=&Conference=&Country=&DateFrom=01/01/{start_year}&DateTo=12/31/{start_year}'
                               f'&Division=&DraftPick=&DraftYear=&GameScope=&Height=&ISTRound=&LastNGames=0&LeagueID=00&Location=&Month=0&OpponentTeamID=0&Outcome='
                               f'&PORound=0&PerMode=Totals&PlayerExperience=&PlayerOrTeam=Team&PlayerPosition=&PtMeasureType=Passing&Season={year}&SeasonSegment='
                               f'&SeasonType={season_type}&StarterBench=&TeamID=0&VsConference=&VsDivision=&Weight=')

        yield Request(url=tracking_passed_url, callback=self.parse_passing, dont_filter=True,
                      headers=self.json_headers, meta=response.meta)

    def parse_passing(self, response):
        print('parse_passing\n\n\n')
        year, season_type, start_year, teams_stats = self.get_teams_stats(response)
        
        if len(teams_stats) == 0:
            return

        for team_stat in teams_stats:
            try:
                team_id = team_stat.get('TEAM_ID', 0.0)
                passes_made = team_stat.get('PASSES_MADE', 0.0)

                player_key = f'{year}_{team_id}_{season_type}'
                if player_key in self.teams_dict:
                    self.teams_dict[player_key]['PASSES_MADE'] = passes_made
                else:
                    item = OrderedDict()
                    item['TEAM_ID'] = team_stat.get('TEAM_ID', 0)
                    item['TEAM_NAME'] = team_stat.get('TEAM_NAME', '')
                    item['PASSES_MADE'] = passes_made
                    item['GAME_TYPE'] = season_type
                    item['DATE'] = f'01/01/{start_year}'
                    item['SEASON'] = year

                    dict_key = f"{item['SEASON']}_{item['TEAM_ID']}_{item['GAME_TYPE']}"
                    self.teams_dict[dict_key] = item

            except:
                a=1

        tracking_touches_url = (f'https://stats.nba.com/stats/leaguedashptstats?College=&Conference=&Country=&DateFrom=01/01/{start_year}&DateTo=12/31/{start_year}'
                                f'&Division=&DraftPick=&DraftYear='
                                f'&GameScope=&Height=&ISTRound=&LastNGames=0&LeagueID=00&Location=&Month=0&OpponentTeamID=0&Outcome=&PORound=0&PerMode=Totals'
                                f'&PlayerExperience=&PlayerOrTeam=Team&PlayerPosition=&PtMeasureType=Possessions&Season={year}&SeasonSegment=&SeasonType={season_type}'
                                f'&StarterBench=&TeamID=0&VsConference=&VsDivision=&Weight=')
        yield Request(url=tracking_touches_url, callback=self.parse_touches, dont_filter=True,
                      headers=self.json_headers, meta=response.meta)

    def parse_touches(self, response):
        print('parse_touches\n\n\n')
        year, season_type, start_year, teams_stats = self.get_teams_stats(response)

        if len(teams_stats) == 0:
            return

        for team_stat in teams_stats:
            try:
                team_id = team_stat.get('TEAM_ID', 0.0)
                sec_touch = team_stat.get('AVG_SEC_PER_TOUCH', 0.0)

                player_key = f'{year}_{team_id}_{season_type}'
                if player_key in self.teams_dict:
                    self.teams_dict[player_key]['SEC_TOUCH'] = sec_touch
                else:
                    item = OrderedDict()
                    item['TEAM_ID'] = team_stat.get('TEAM_ID', 0)
                    item['TEAM_NAME'] = team_stat.get('TEAM_NAME', '')
                    item['SEC_TOUCH'] = sec_touch
                    item['GAME_TYPE'] = season_type
                    item['SEASON'] = year
                    item['DATE'] = f'01/01/{start_year}'

                    dict_key = f"{item['SEASON']}_{item['TEAM_ID']}_{item['GAME_TYPE']}"
                    self.teams_dict[dict_key] = item

            except:
                a=1

        tracking_rebounding_url = (
            f'https://stats.nba.com/stats/leaguedashptstats?College=&Conference=&Country=&DateFrom=01/01/{start_year}&DateTo=12/31/{start_year}'
            f'&Division=&DraftPick=&DraftYear=&'
            f'GameScope=&Height=&ISTRound=&LastNGames=0&LeagueID=00&Location=&Month=0&OpponentTeamID=0&Outcome=&PORound=0&PerMode=Totals&PlayerExperience='
            f'&PlayerOrTeam=Team&PlayerPosition=&PtMeasureType=Rebounding&Season={year}&SeasonSegment=&SeasonType={season_type}&StarterBench=&TeamID=0'
            f'&VsConference=&VsDivision=&Weight=')

        yield Request(url=tracking_rebounding_url, callback=self.parse_rebounding,
                      dont_filter=True, headers=self.json_headers, meta=response.meta)

    def parse_rebounding(self, response):
        print('parse_rebounding\n\n\n')
        year, season_type, start_year, teams_stats = self.get_teams_stats(response)

        for team_stat in teams_stats:
            try:
                team_id = team_stat.get('TEAM_ID', 0.0)
                reb_chance = team_stat.get('REB_CHANCE_PCT_ADJ', 0.0)
                reb_chance = reb_chance * 100
                reb_chance = "{:.2f}".format(reb_chance)

                player_key = f'{year}_{team_id}_{season_type}'
                if player_key in self.teams_dict:
                    self.teams_dict[player_key]['ADJ_REB_CHANCE_%'] = reb_chance
                else:
                    item = OrderedDict()
                    item['TEAM_ID'] = team_stat.get('TEAM_ID', 0)
                    item['TEAM_NAME'] = team_stat.get('TEAM_NAME', '')
                    item['ADJ_REB_CHANCE_%'] = reb_chance
                    item['GAME_TYPE'] = season_type
                    item['SEASON'] = year
                    item['DATE'] = f'01/01/{start_year}'

                    dict_key = f"{item['SEASON']}_{item['TEAM_ID']}_{item['GAME_TYPE']}"
                    self.teams_dict[dict_key] = item
            except:
                a=1

        tracking_offencive_rebounding_url = (
            f'https://stats.nba.com/stats/leaguedashptstats?College=&Conference=&Country=&DateFrom=01/01/{start_year}&DateTo=12/31/{start_year}'
            f'&Division=&DraftPick='
            f'&DraftYear=&GameScope=&Height=&ISTRound=&LastNGames=0&LeagueID=00&Location=&Month=0&OpponentTeamID=0&Outcome=&PORound=0'
            f'&PerMode=Totals&PlayerExperience=&PlayerOrTeam=Team&PlayerPosition=&PtMeasureType=Rebounding&Season={year}&'
            f'SeasonSegment=&SeasonType={season_type}&StarterBench=&TeamID=0&VsConference=&VsDivision=&Weight=')

        yield Request(url=tracking_offencive_rebounding_url, callback=self.parse_offensive_rebounding, dont_filter=True,
                      headers=self.json_headers, meta=response.meta)

    def parse_offensive_rebounding(self, response):
        print('parse_offensive_rebounding\n\n\n')
        year, season_type, start_year, teams_stats = self.get_teams_stats(response)

        for team_stat in teams_stats:
            try:
                team_id = team_stat.get('TEAM_ID', 0.0)
                adj_oreb_chance = team_stat.get('OREB_CHANCE_PCT_ADJ', 0.0)
                adj_oreb_chance = adj_oreb_chance * 100
                adj_oreb_chance = "{:.2f}".format(adj_oreb_chance)

                player_key = f'{year}_{team_id}_{season_type}'
                if player_key in self.teams_dict:
                    self.teams_dict[player_key]['ADJ_OFF_REB_CHANCE_%'] = adj_oreb_chance
                else:
                    item = OrderedDict()
                    item['TEAM_ID'] = team_stat.get('TEAM_ID', 0)
                    item['TEAM_NAME'] = team_stat.get('TEAM_NAME', '')
                    item['ADJ_OFF_REB_CHANCE_%'] = adj_oreb_chance
                    item['GAME_TYPE'] = season_type
                    item['SEASON'] = year
                    item['DATE'] = f'01/01/{start_year}'

                    dict_key = f"{item['SEASON']}_{item['TEAM_ID']}_{item['GAME_TYPE']}"
                    self.teams_dict[dict_key] = item
            except:
                a=1

        tracking_defencive_rebounding_url = (
            f'https://stats.nba.com/stats/leaguedashptstats?College=&Conference=&Country=&DateFrom=01/01/{start_year}&DateTo=12/31/{start_year}&Division=&DraftPick=&'
            f'DraftYear=&GameScope=&Height=&ISTRound=&LastNGames=0&LeagueID=00&Location=&Month=0&OpponentTeamID=0&Outcome=&PORound=0'
            f'&PerMode=Totals&PlayerExperience=&PlayerOrTeam=Team&PlayerPosition=&PtMeasureType=Rebounding&'
            f'Season={year}&SeasonSegment=&SeasonType={season_type}&StarterBench=&TeamID=0&VsConference=&VsDivision=&Weight=')

        yield Request(url=tracking_defencive_rebounding_url, callback=self.parse_defensive_rebounding,
                      dont_filter=True, headers=self.json_headers, meta=response.meta)

    def parse_defensive_rebounding(self, response):
        print('parse_defensive_rebounding\n\n\n')
        year, season_type, start_year, teams_stats = self.get_teams_stats(response)

        for team_stat in teams_stats:
            try:
                team_id = team_stat.get('TEAM_ID', 0.0)
                adj_reb_chance = team_stat.get('DREB_CHANCE_PCT_ADJ', 0.0)
                adj_reb_chance = adj_reb_chance * 100
                adj_reb_chance = "{:.2f}".format(adj_reb_chance)

                player_key = f'{year}_{team_id}_{season_type}'

                if player_key in self.teams_dict:
                    self.teams_dict[player_key]['ADJ_DEF_REB_CHANCE_%'] = adj_reb_chance
                else:
                    item = OrderedDict()
                    item['TEAM_ID'] = team_stat.get('TEAM_ID', 0)
                    item['TEAM_NAME'] = team_stat.get('TEAM_NAME', '')
                    item['ADJ_DEF_REB_CHANCE_%'] = adj_reb_chance

                    item['GAME_TYPE'] = season_type
                    item['SEASON'] = year
                    item['DATE'] = f'01/01/{start_year}'

                    dict_key = f"{item['SEASON']}_{item['TEAM_ID']}_{item['GAME_TYPE']}"
                    self.teams_dict[dict_key] = item

            except:
                a=1

        tracking_speed_distance_url = (
            f'https://stats.nba.com/stats/leaguedashptstats?College=&Conference=&Country=&DateFrom=01/01/{start_year}&DateTo=12/31/{start_year}&Division=&DraftPick=&'
            f'DraftYear=&GameScope=&Height=&ISTRound=&LastNGames=0&LeagueID=00&Location=&Month=0&OpponentTeamID=0&Outcome=&PORound=0&'
            f'PerMode=Totals&PlayerExperience=&PlayerOrTeam=Team&PlayerPosition=&PtMeasureType=SpeedDistance&Season={year}'
            f'&SeasonSegment=&SeasonType={season_type}&StarterBench=&TeamID=0&VsConference=&VsDivision=&Weight=')

        yield Request(url=tracking_speed_distance_url, callback=self.parse_speed_distance,
                      dont_filter=True, headers=self.json_headers, meta=response.meta)

    def parse_speed_distance(self, response):
        print('Tracking/Speed and Distance \n\n\n')
        year, season_type, start_year, teams_stats = self.get_teams_stats(response)

        for team_stat in teams_stats:
            try:
                team_id = team_stat.get('TEAM_ID', 0.0)
                avg_speed = team_stat.get('AVG_SPEED_OFF', 0.0)

                player_key = f'{year}_{team_id}_{season_type}'
                if player_key in self.teams_dict:
                    self.teams_dict[player_key]['AVG_SPEED_OFF'] = avg_speed
                else:
                    item = OrderedDict()
                    item['TEAM_ID'] = team_stat.get('TEAM_ID', 0)
                    item['TEAM_NAME'] = team_stat.get('TEAM_NAME', '')
                    item['AVG_SPEED_OFF'] = avg_speed

                    item['GAME_TYPE'] = season_type
                    item['SEASON'] = year
                    item['DATE'] = f'01/01/{start_year}'

                    dict_key = f"{item['SEASON']}_{item['TEAM_ID']}_{item['GAME_TYPE']}"
                    self.teams_dict[dict_key] = item
            except:
                a=1

        shooting_distance_zone_url = (f'https://stats.nba.com/stats/leaguedashteamshotlocations?Conference=&DateFrom=01/01/{start_year}&DateTo=12/31/{start_year}'
                                      f'&DistanceRange=By Zone&Division=&GameScope=&GameSegment=&ISTRound=&LastNGames=0&Location=&MeasureType=Base&Month=0'
                                      f'&OpponentTeamID=0&Outcome=&PORound=0&PaceAdjust=N&PerMode=Totals&Period=0&PlayerExperience=&PlayerPosition=&PlusMinus=N'
                                      f'&Rank=N&Season={year}&SeasonSegment=&SeasonType={season_type}&ShotClockRange=&StarterBench=&TeamID=0&VsConference=&VsDivision=')

        yield Request(url=shooting_distance_zone_url, callback=self.parse_distance_zone,
                      dont_filter=True, headers=self.json_headers, meta=response.meta)

    def parse_distance_zone(self, response):
        print('Shooting/Distance Range==By Zone \n\n\n')
        year = response.meta.get('year')
        start_year = year.split('-')[0]
        season_type = response.meta.get('season_type', '')

        try:
            data_dict = response.json()
        except json.JSONDecodeError as e:
            data_dict = {}
            a = 1

        headers = [headers for headers in data_dict.get('resultSets', {}).get('headers', []) if
                   headers.get('name', '') == 'columns'][0].get('columnNames', [])
        records = data_dict.get('resultSets', {}).get('rowSet', [])

        teams_stats = []

        for record in records:
            record_dict = {}
            for i, header in enumerate(headers):
                # Using enumerate to ensure the i-th header maps to the i-th value in the record
                if header in record_dict:
                    # If the header already exists, we create a numbered version of it to avoid overwriting
                    counter = 1
                    new_header = f"{header}_{counter}"
                    while new_header in record_dict:
                        counter += 1
                        new_header = f"{header}_{counter}"
                    record_dict[new_header] = record[i]
                else:
                    record_dict[header] = record[i]

            teams_stats.append(record_dict)

        for team_stats in teams_stats:
            item = OrderedDict()
            item['FGM_RA'] = team_stats.get('FGM', 0.0)
            item['FGA_RA'] = team_stats.get('FGA', 0.0)
            item['FGM_PAINT'] = team_stats.get('FGM_1', 0.0)
            item['FGA_PAINT'] = team_stats.get('FGA_1', 0.0)
            item['FGM_MID-RANGE'] = team_stats.get('FGM_2', 0.0)
            item['FGA_MID-RANGE'] = team_stats.get('FGA_2', 0.0)
            item['FGM_CORNER'] = team_stats.get('FGM_7', 0.0)
            item['FGA_CORNER'] = team_stats.get('FGA_7', 0.0)
            item['FGM_AB'] = team_stats.get('FGM_5', 0.0)
            item['FGA_AB'] = team_stats.get('FGA_5', 0.0)

            team_id = team_stats.get('TEAM_ID', 0.0)

            player_key = f'{year}_{team_id}_{season_type}'
            if player_key in self.teams_dict:
                self.teams_dict[player_key].update(item)

        hustle_url = (f'https://stats.nba.com/stats/leaguehustlestatsteam?College=&Conference=&Country=&DateFrom=01/01/{start_year}&DateTo=12/31/{start_year}'
              f'&Division=&DraftPick=&DraftYear=&GameScope=&Height=&ISTRound=&LastNGames=0&LeagueID=00&Location=&Month=0&OpponentTeamID=0'
              f'&Outcome=&PORound=0&PaceAdjust=N&PerMode=Totals&PlayerExperience=&PlayerPosition=&PlusMinus=N&Rank=N&Season={year}'
              f'&SeasonSegment=&SeasonType={season_type}&ShotClockRange=&TeamID=0&VsConference=&VsDivision=&Weight=')

        yield Request(url=hustle_url, callback=self.parse_hustle,
                      dont_filter=True, headers=self.json_headers, meta=response.meta)

    def parse_hustle(self, response):
        print('parse_hustle \n\n\n')

        # team not exist
        year = response.meta.get('year')
        start_year = year.split('-')[0]
        season_type = response.meta.get('season_type', '')

        try:
            res_dict = response.json()
        except json.JSONDecodeError as e:
            res_dict = {}
            a = 1

        try:
            teams_stats = res_dict.get('resultSets', [])[0].get('rowSet', [])
        except (IndexError, AttributeError):
            teams_stats = []

        for team_stats in teams_stats:
            try:
                deflections = team_stats[10]
                screen_ast_pt = team_stats[13]

                team_id = team_stats[0]

                player_key = f'{year}_{team_id}_{season_type}'
                if player_key in self.teams_dict:
                    self.teams_dict[player_key]['DEFLECTIONS'] = deflections
                    self.teams_dict[player_key]['SCREEN_AST_PTS'] = screen_ast_pt

                else:
                    print('Player not exist')
            except:
                a=1

        shooting_efficiency_url = (
            f'https://stats.nba.com/stats/leaguedashptstats?College=&Conference=&Country=&DateFrom=01/01/{start_year}&DateTo=12/31/{start_year}'
            f'&Division=&DraftPick='
            f'&DraftYear=&GameScope=&Height=&ISTRound=&LastNGames=0&LeagueID=00&Location=&Month=0&OpponentTeamID=0&Outcome=&PORound=0'
            f'&PerMode=Totals&PlayerExperience=&PlayerOrTeam=Team&PlayerPosition=&PtMeasureType=Efficiency&Season={year}'
            f'&SeasonSegment=&SeasonType={season_type}&StarterBench=&TeamID=0&VsConference=&VsDivision=&Weight=')

        yield Request(url=shooting_efficiency_url, callback=self.parse_shooting_efficiency,
                      dont_filter=True, headers=self.json_headers, meta=response.meta)

    def parse_shooting_efficiency(self, response):
        print('parse_shooting_efficiency \n\n\n')
        year, season_type, start_year, teams_stats = self.get_teams_stats(response)

        for team_stats in teams_stats:
            item = OrderedDict()
            item['DRIVE_PTS'] = team_stats.get('DRIVE_PTS', 0.0)
            item['C&S_PTS'] = team_stats.get('CATCH_SHOOT_PTS', 0.0)
            item['PULL_UP_PTS'] = team_stats.get('PULL_UP_PTS', 0.0)
            item['PAINT_TOUCH_PTS'] = team_stats.get('PAINT_TOUCH_PTS', 0.0)
            item['POST_TOUCH_PTS'] = team_stats.get('POST_TOUCH_PTS', 0.0)
            item['ELBOW_TOUCH_PTS'] = team_stats.get('ELBOW_TOUCH_PTS', 0.0)

            team_id = team_stats.get('TEAM_ID', 0.0)

            player_key = f'{year}_{team_id}_{season_type}'
            if player_key in self.teams_dict:
                self.teams_dict[player_key].update(item)

        self.write_to_player_csv(year)

        # defense_dash_2_points_url =  (f'https://stats.nba.com/stats/leaguedashptteamdefend?Conference=&DateFrom=01/01/{start_year}&DateTo=12/31/{start_year}'
        #      f'&DefenseCategory=2 Pointers&Division=&GameSegment=&LastNGames=0&LeagueID=00&Location=&Month=0&OpponentTeamID=0&Outcome='
        #      f'&PORound=0&PerMode=PerGame&Period=0&Season={year}&SeasonSegment=&SeasonType={season_type}&TeamID=0&VsConference=&VsDivision=')

        # yield Request(url=defense_dash_2_points_url, callback=self.parse_defense_dash_2_points,
        #               dont_filter=True, headers=self.json_headers, meta=response.meta)

    def parse_defense_dash_2_points(self, response):
        print('parse_defense_dash_2_points \n\n\n')
        year, season_type, start_year, teams_stats = self.get_teams_stats(response)

        for team_stats in teams_stats:
            try:
                item = OrderedDict()

                fg = team_stats.get('FG2_PCT', 0.0)
                freq = team_stats.get('FREQ', 0.0)
                freq = "{:.2f}".format(freq * 100)
                item['OPP_2PT_FREQ_%'] = freq
                item['OPP_2PT_DFGM'] = team_stats.get('FG2M', 0.0)
                item['OPP_2PT_DFGA'] = team_stats.get('FG2A', 0.0)
                item['OPP_2PT_FG_%'] = fg * 100

                # team not exist check this key
                team_id = team_stats.get('TEAM_ID', 0)

                player_key = f'{year}_{team_id}_{season_type}'
                if player_key in self.teams_dict:
                    self.teams_dict[player_key].update(item)

                else:
                    print('Not matched records Dash 2')
            except:
                a=1

        defense_dash_3_points_url = (f'https://stats.nba.com/stats/leaguedashptteamdefend?Conference=&DateFrom=01/01/{start_year}&DateTo=12/31/{start_year}'
             f'&DefenseCategory=3 Pointers&Division=&GameSegment=&LastNGames=0&LeagueID=00&Location=&Month=0&OpponentTeamID=0&Outcome=&PORound=0'
             f'&PerMode=PerGame&Period=0&Season={year}&SeasonSegment=&SeasonType={season_type}&TeamID=0&VsConference=&VsDivision=')

        yield Request(url=defense_dash_3_points_url, callback=self.parse_defense_dash_3_points,
                      dont_filter=True, headers=self.json_headers, meta=response.meta)

    def parse_defense_dash_3_points(self, response):
        print('parse_defense_dash_3_points \n\n\n')
        year, season_type, start_year, teams_stats = self.get_teams_stats(response)

        for team_stats in teams_stats:
            item = OrderedDict()

            freq = team_stats.get('FREQ', 0.0)
            fg = team_stats.get('FG3_PCT', 0.0)
            item['OPP_3PT_DFGA'] = team_stats.get('FG3A', 0.0)
            item['OPP_3PT_FREQ_%'] = freq * 100
            item['OPP_3PT_FG_%'] = fg * 100
            item['OPP_3PT_DFGM'] = team_stats.get('FG3M', 0.0)

            # team not exist check tjhis key
            team_id = team_stats.get('TEAM_ID', 0)

            player_key = f'{year}_{team_id}_{season_type}'
            if player_key in self.teams_dict:
                self.teams_dict[player_key].update(item)

            else:
                print('Records NOt matched Dash 3 points')

        self.write_to_player_csv(year)

    def write_to_player_csv(self, year):
        folder_path = "TEAM"
        os.makedirs(folder_path, exist_ok=True)

        # Iterate player data
        for team_id, team_record in self.teams_dict.items():
            team_name = team_record.get('TEAM_NAME', '').upper()
            team_name_clean = team_name.replace('.', '').replace("'", "")

            filename = os.path.join(folder_path, f"{team_name_clean}.csv")

            # Check if the file exists to append or create a new one
            file_exists = os.path.isfile(filename)

            with open(filename, mode='a' if file_exists else 'w', newline='', encoding='utf-8') as csvfile:
                csv_writer = csv.DictWriter(csvfile, fieldnames=self.team_csv_headers)

                # Write headers if the file is new
                if not file_exists or csvfile.tell() == 0:
                    csv_writer.writeheader()

                # Write the player's data (ensure it's in the correct format)
                csv_writer.writerow(team_record)

                # self.logger.info(f"Saved data for {item.get('Name')} to {filename}")
                print(f"Saved data for {team_name} to {filename}")

        # CSV file to hold all player records
        combined_filename = os.path.join(folder_path, f'{year}.csv')

        # Check if the combined file exists to append or create a new one
        combined_file_exists = os.path.isfile(combined_filename)

        # Open the combined file in append mode or write mode if it doesn't exist
        with open(combined_filename, mode='a' if combined_file_exists else 'w', newline='',
                  encoding='utf-8') as combined_csvfile:
            combined_csv_writer = csv.DictWriter(combined_csvfile, fieldnames=self.team_csv_headers)

            # Write headers for the combined file if it doesn't exist or is empty
            if not combined_file_exists or combined_csvfile.tell() == 0:
                combined_csv_writer.writeheader()

            # Write each player's filtered data to the combined file
            for player_record in self.teams_dict.values():
                filtered_record = {key: player_record.get(key, '') for key in self.team_csv_headers}
                combined_csv_writer.writerow(filtered_record)

            print(f"Saved all player data to {combined_filename}")

    def get_teams_stats(self, response):
        year = response.meta.get('year')
        season_type = response.meta.get('season_type')
        start_year = year.split('-')[0]

        try:
            res_dict = response.json()
        except json.JSONDecodeError as e:
            res_dict = {}
            return

        parameters_info = res_dict.get('parameters', {})
        # cat_name = parameters_info.get('MeasureType') or parameters_info.get('PtMeasureType', '')
        # season = parameters_info.get('Season', '')

        try:
            data_dict = res_dict.get('resultSets', [{}])[0]
        except:
            data_dict = {}

        headers = data_dict.get('headers', [])
        teams_stats = [dict(zip(headers, row)) for row in data_dict['rowSet']]

        if len(teams_stats) == 0:
            a=1

        return year, season_type, start_year, teams_stats
        # return teams_stats or []

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(NbaTeamSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_idle, signal=signals.spider_idle)
        return spider

    def spider_idle(self):
        self.teams_dict = {}
        if self.years_range:
            year = self.years_range.pop()
            req = Request(url='http://books.toscrape.com/',
                          callback=self.parse,
                          dont_filter=True,
                          meta={'handle_httpstatus_all': True, 'year': year})

            try:
                self.crawler.engine.crawl(req)  # For latest Python version
            except TypeError:
                self.crawler.engine.crawl(req, self)  # For old Python version < 10
