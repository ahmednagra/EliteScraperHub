import json
import os
import csv
from collections import OrderedDict
from typing import Any

from scrapy import Spider, Request, signals
from scrapy.http import Response


class NbaPlayerSpider(Spider):
    name = 'nba_player'
    base_url = 'https://www.nba.com/'

    player_csv_headers = ['ID', 'Name', 'Nick Name', 'TEAM_ID', 'TEAM_ABBREVIATION', 'DATE', 'SEASON', 'GAME_TYPE',
                          'PACE', 'PIE',
                          'PASSES_MADE', 'SEC_TOUCH', 'ADJ_REB_CHANCE_%',
                          'ADJ_OFF_REB_CHANCE_%', 'ADJ_DEF_REB_CHANCE_%', 'AVG_SPEED_OFF', 'FGM_RA', 'FGA_RA',
                          'FGM_PAINT',
                          'FGA_PAINT', 'FGM_MID-RANGE', 'FGA_MID-RANGE', 'FGM_CORNER', 'FGA_CORNER', 'FGM_AB', 'FGA_AB',
                          'DEFLECTIONS', 'SCREEN_AST_PTS', 'DRIVE_PTS', 'C&S_PTS', 'PULL_UP_PTS', 'PAINT_TOUCH_PTS',
                          'POST_TOUCH_PTS', 'ELBOW_TOUCH_PTS',
                          'OPP_2PT_FREQ_%', 'OPP_2PT_DFGM', 'OPP_2PT_DFGA', 'OPP_2PT_FG_%',
                          'OPP_3PT_DFGA', 'OPP_3PT_FREQ_%', 'OPP_3PT_FG_%', 'OPP_3PT_DFGM']

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
        self.players_dict = {}
        self.years_range = [
            '2024-25', '2023-24', '2022-23', '2021-22', '2020-21',
            '2019-20', '2018-19', '2017-18', '2016-17', '2015-16'
        ]

    def start_requests(self):
        yield from self.spider_idle

    def parse(self, response: Response, **kwargs: Any) -> Any:
        year = response.meta.get('year')
        season_types = [
            ('Playoffs', 'Playoffs'),
            ('All Star', 'All-Star'),
            ('PlayIn', 'Play In'),
            ('IST', 'NBA Cup'),
            # ('Pre Season', 'Preseason'),
            ('Regular Season', 'Regular Season')
        ]

        # for season_type in seas:
        print(f'year : {year}')
        start_year = year.split('-')[0]
            # for val, text in season_type:
                # print(f'Value {val} & Text: {text}')
                # general_advanced_url = 'https://stats.nba.com/stats/leaguedashplayerstats?College=&Conference=&Country=&DateFrom=&DateTo=&Division=&DraftPick=&DraftYear=&GameScope=&GameSegment=&Height=&ISTRound=&LastNGames=0&LeagueID=00&Location=&MeasureType=Advanced&Month=0&OpponentTeamID=0&Outcome=&PORound=0&PaceAdjust=N&PerMode=PerGame&Period=0&PlayerExperience=&PlayerPosition=&PlusMinus=N&Rank=N&Season=2015-16&SeasonSegment=&SeasonType=Pre%20Season&ShotClockRange=&StarterBench=&TeamID=0&VsConference=&VsDivision=&Weight='
                # general_advanced_url = (f'https://stats.nba.com/stats/leaguedashplayerstats?College=&Conference=&Country='
                #                         f'&DateFrom=01/01/{start_year}&DateTo=12/31/{start_year}&Division=&DraftPick=&DraftYear=&GameScope='
                #                         f'&GameSegment=&Height=&ISTRound=&LastNGames=0&LeagueID=00&Location=&MeasureType=Base'
                #                         f'&Month=0&OpponentTeamID=0&Outcome=&PORound=0&PaceAdjust=N&PerMode=Totals&Period=0'
                #                         f'&PlayerExperience=&PlayerPosition=&PlusMinus=N&Rank=N&Season={year}&SeasonSegment='
                #                         f'&SeasonType={val}&ShotClockRange=&StarterBench=&TeamID=0&VsConference=&VsDivision=&Weight=')
        general_advanced_url = (f'https://stats.nba.com/stats/leaguedashplayerstats?College=&Conference=&Country='
                                f'&DateFrom=01/01/{start_year}&DateTo=12/31/{start_year}&Division=&DraftPick=&DraftYear=&GameScope='
                                f'&GameSegment=&Height=&ISTRound=&LastNGames=0&LeagueID=00&Location=&MeasureType=Base'
                                f'&Month=0&OpponentTeamID=0&Outcome=&PORound=0&PaceAdjust=N&PerMode=Totals&Period=0'
                                f'&PlayerExperience=&PlayerPosition=&PlusMinus=N&Rank=N&Season={year}&SeasonSegment='
                                f'&SeasonType=Regular Season&ShotClockRange=&StarterBench=&TeamID=0&VsConference=&VsDivision=&Weight=')
        text = 'Regular Season'
        yield Request(url=general_advanced_url, callback=self.parse_advance, dont_filter=True,
                      headers=self.json_headers, meta={'year': year, 'season_type': text})

    def parse_advance(self, response):
        print('parse_advance\n\n\n')
        year = response.meta.get('year')
        season_type = response.meta.get('season_type')
        start_year = year.split('-')[0]
        players_stats = self.get_players_stats(response)

        print(f'Year :{year} Season Type:{season_type}')
        if len(players_stats) == 0:
            return

        for player_stat in players_stats:
            try:
                item = OrderedDict()
                item['ID'] = player_stat.get('PLAYER_ID', 0)
                item['Name'] = player_stat.get('PLAYER_NAME', '')
                item['Nick Name'] = player_stat.get('NICKNAME', '')
                item['TEAM_ID'] = player_stat.get('TEAM_ID', 0)
                item['TEAM_ABBREVIATION'] = player_stat.get('TEAM_ABBREVIATION', '')
                item['SEASON'] = year
                item['GAME_TYPE'] = season_type
                item['DATE'] = f'01/01/{start_year}'
                item['PACE'] = player_stat.get('PACE', 0.0)
                item['PIE'] = player_stat.get('PIE', 0.0)

                dict_key = f"{item['SEASON']}_{item['ID']}_{item['GAME_TYPE']}"
                # dict_key = f"{item['SEASON']}_{item['ID']}"
                self.players_dict[dict_key] = item

            except:
                a=1

        tracking_passed_url = (f'https://stats.nba.com/stats/leaguedashptstats?College=&Conference=&Country=&DateFrom=01/01/{start_year}&DateTo=12/31/{start_year}'
                               f'&Division=&DraftPick=&DraftYear=&GameScope=&Height=&ISTRound=&LastNGames=0&LeagueID=00&Location=&Month=0&OpponentTeamID=0&Outcome='
                               f'&PORound=0&PerMode=PerGame&PlayerExperience=&PlayerOrTeam=Player&PlayerPosition=&PtMeasureType=Passing&Season={year}&SeasonSegment='
                               f'&SeasonType=Regular Season&StarterBench=&TeamID=0&VsConference=&VsDivision=&Weight=')
        yield Request(url=tracking_passed_url, callback=self.parse_passing, dont_filter=True,
                      headers=self.json_headers, meta=response.meta)

    def parse_passing(self, response):
        print('parse_passing\n\n\n')
        year = response.meta.get('year')
        start_year = year.split('-')[0]
        game_type = response.meta.get('season_type', '')
        players_stats = self.get_players_stats(response)

        if len(players_stats) == 0:
            return

        for player_stat in players_stats:
            try:
                player_id = player_stat.get('PLAYER_ID', 0.0)
                passes_made = player_stat.get('PASSES_MADE', 0.0)

                player_key = f'{year}_{player_id}_{game_type}'
                if player_key in self.players_dict:
                    self.players_dict[player_key]['PASSES_MADE'] = passes_made
                else:
                    item = OrderedDict()
                    item['ID'] = player_stat.get('PLAYER_ID', 0)
                    item['Name'] = player_stat.get('PLAYER_NAME', '')
                    item['Nick Name'] = player_stat.get('NICKNAME', '')
                    item['TEAM_ID'] = player_stat.get('TEAM_ID', 0)
                    item['TEAM_ABBREVIATION'] = player_stat.get('TEAM_ABBREVIATION', '')
                    item['PASSES_MADE'] = passes_made
                    item['GAME_TYPE'] = game_type
                    item['DATE'] = f'01/01/{start_year}'
                    item['SEASON'] = year

                    dict_key = f"{item['SEASON']}_{item['ID']}_{item['GAME_TYPE']}"
                    self.players_dict[dict_key] = item

            except:
                a=1

        tracking_touches_url = f'https://stats.nba.com/stats/leaguedashptstats?College=&Conference=&Country=&DateFrom=&DateTo=&Division=&DraftPick=&DraftYear=&GameScope=&Height=&ISTRound=&LastNGames=0&LeagueID=00&Location=&Month=0&OpponentTeamID=0&Outcome=&PORound=0&PerMode=PerGame&PlayerExperience=&PlayerOrTeam=Player&PlayerPosition=&PtMeasureType=Possessions&Season={year}&SeasonSegment=&SeasonType=Playoffs&StarterBench=&TeamID=0&VsConference=&VsDivision=&Weight='
        yield Request(url=tracking_touches_url, callback=self.parse_touches, dont_filter=True,
                      headers=self.json_headers, meta=response.meta)

    def parse_touches(self, response):
        print('parse_touches\n\n\n')
        year = response.meta.get('year', '')
        start_year = year.split('-')[0]
        game_type = response.meta.get('season_type', '')
        players_stats = self.get_players_stats(response)

        if len(players_stats) == 0:
            return

        for player_stat in players_stats:
            try:
                player_id = player_stat.get('PLAYER_ID', 0.0)
                sec_touch = player_stat.get('AVG_SEC_PER_TOUCH', 0.0)

                player_key = f'{year}_{player_id}_{game_type}'
                if player_key in self.players_dict:
                    self.players_dict[player_key]['SEC_TOUCH'] = sec_touch
                else:
                    item = OrderedDict()
                    item['ID'] = player_stat.get('PLAYER_ID', 0)
                    item['Name'] = player_stat.get('PLAYER_NAME', '')
                    item['Nick Name'] = player_stat.get('NICKNAME', '')
                    item['TEAM_ID'] = player_stat.get('TEAM_ID', 0)
                    item['SEC_TOUCH'] = sec_touch
                    item['GAME_TYPE'] = game_type
                    item['SEASON'] = year
                    item['DATE'] = f'01/01/{start_year}'

                    dict_key = f"{item['SEASON']}_{item['ID']}_{item['GAME_TYPE']}"
                    self.players_dict[dict_key] = item

            except:
                a=1

        tracking_rebounding_url = (
            f'https://stats.nba.com/stats/leaguedashptstats?College=&Conference=&Country=&DateFrom=&DateTo=&Division=&DraftPick=&DraftYear=&'
            f'GameScope=&Height=&ISTRound=&LastNGames=0&LeagueID=00&Location=&Month=0&OpponentTeamID=0&Outcome=&PORound=0&PerMode=PerGame&PlayerExperience='
            f'&PlayerOrTeam=Player&PlayerPosition=&PtMeasureType=Rebounding&Season={year}&SeasonSegment=&SeasonType=Playoffs&StarterBench=&TeamID=0'
            f'&VsConference=&VsDivision=&Weight=')

        yield Request(url=tracking_rebounding_url, callback=self.parse_rebounding,
                      dont_filter=True, headers=self.json_headers, meta=response.meta)

    def parse_rebounding(self, response):
        print('parse_rebounding\n\n\n')
        year = response.meta.get('year')
        start_year = year.split('-')[0]
        game_type = response.meta.get('season_type', '')
        players_stats = self.get_players_stats(response)

        for player_stat in players_stats:
            try:
                player_id = player_stat.get('PLAYER_ID', 0.0)
                reb_chance = player_stat.get('REB_CHANCE_PCT_ADJ', 0.0)
                reb_chance = reb_chance * 100
                reb_chance = "{:.2f}".format(reb_chance)

                player_key = f'{year}_{player_id}_{game_type}'
                if player_key in self.players_dict:
                    self.players_dict[player_key]['ADJ_REB_CHANCE_%'] = reb_chance
                else:
                    item = OrderedDict()
                    item['ID'] = player_stat.get('PLAYER_ID', 0)
                    item['Name'] = player_stat.get('PLAYER_NAME', '')
                    item['Nick Name'] = player_stat.get('NICKNAME', '')
                    item['TEAM_ID'] = player_stat.get('TEAM_ID', 0)
                    item['ADJ_REB_CHANCE_%'] = reb_chance
                    item['GAME_TYPE'] = game_type
                    item['SEASON'] = year
                    item['DATE'] = f'01/01/{start_year}'

                    dict_key = f"{item['SEASON']}_{item['ID']}_{item['GAME_TYPE']}"
                    self.players_dict[dict_key] = item
            except:
                a=1

        tracking_offencive_rebounding_url = (
            f'https://stats.nba.com/stats/leaguedashptstats?College=&Conference=&Country=&DateFrom=&DateTo=&Division=&DraftPick='
            f'&DraftYear=&GameScope=&Height=&ISTRound=&LastNGames=0&LeagueID=00&Location=&Month=0&OpponentTeamID=0&Outcome=&PORound=0'
            f'&PerMode=PerGame&PlayerExperience=&PlayerOrTeam=Player&PlayerPosition=&PtMeasureType=Rebounding&Season={year}&'
            f'SeasonSegment=&SeasonType=Playoffs&StarterBench=&TeamID=0&VsConference=&VsDivision=&Weight=')

        yield Request(url=tracking_offencive_rebounding_url, callback=self.parse_offensive_rebounding, dont_filter=True,
                      headers=self.json_headers, meta=response.meta)

    def parse_offensive_rebounding(self, response):
        print('parse_offensive_rebounding\n\n\n')
        year = response.meta.get('year')
        start_year = year.split('-')[0]
        game_type = response.meta.get('season_type', '')
        players_stats = self.get_players_stats(response)

        for player_stat in players_stats:
            try:
                player_id = player_stat.get('PLAYER_ID', 0.0)
                adj_oreb_chance = player_stat.get('OREB_CHANCE_PCT_ADJ', 0.0)
                adj_oreb_chance = adj_oreb_chance * 100
                adj_oreb_chance = "{:.2f}".format(adj_oreb_chance)

                player_key = f'{year}_{player_id}_{game_type}'
                if player_key in self.players_dict:
                    self.players_dict[player_key]['ADJ_OFF_REB_CHANCE_%'] = adj_oreb_chance
                else:
                    item = OrderedDict()
                    item['ID'] = player_stat.get('PLAYER_ID', 0)
                    item['Name'] = player_stat.get('PLAYER_NAME', '')
                    item['Nick Name'] = player_stat.get('NICKNAME', '')
                    item['TEAM_ID'] = player_stat.get('TEAM_ID', 0)
                    item['ADJ_OFF_REB_CHANCE_%'] = adj_oreb_chance
                    item['GAME_TYPE'] = game_type
                    item['SEASON'] = year
                    item['DATE'] = f'01/01/{start_year}'

                    dict_key = f"{item['SEASON']}_{item['ID']}_{item['GAME_TYPE']}"
                    self.players_dict[dict_key] = item
            except:
                a=1

        tracking_defencive_rebounding_url = (
            f'https://stats.nba.com/stats/leaguedashptstats?College=&Conference=&Country=&DateFrom=&DateTo=&Division=&DraftPick=&'
            f'DraftYear=&GameScope=&Height=&ISTRound=&LastNGames=0&LeagueID=00&Location=&Month=0&OpponentTeamID=0&Outcome=&PORound=0'
            f'&PerMode=PerGame&PlayerExperience=&PlayerOrTeam=Player&PlayerPosition=&PtMeasureType=Rebounding&'
            f'Season={year}&SeasonSegment=&SeasonType=Playoffs&StarterBench=&TeamID=0&VsConference=&VsDivision=&Weight=')

        yield Request(url=tracking_defencive_rebounding_url, callback=self.parse_defensive_rebounding,
                      dont_filter=True, headers=self.json_headers, meta=response.meta)

    def parse_defensive_rebounding(self, response):
        print('parse_defensive_rebounding\n\n\n')
        year = response.meta.get('year')
        start_year = year.split('-')[0]
        game_type = response.meta.get('season_type', '')
        players_stats = self.get_players_stats(response)

        for player_stat in players_stats:
            try:
                player_id = player_stat.get('PLAYER_ID', 0.0)
                adj_reb_chance = player_stat.get('DREB_CHANCE_PCT_ADJ', 0.0)
                adj_reb_chance = adj_reb_chance * 100
                adj_reb_chance = "{:.2f}".format(adj_reb_chance)

                player_key = f'{year}_{player_id}_{game_type}'

                if player_key in self.players_dict:
                    self.players_dict[player_key]['ADJ_DEF_REB_CHANCE_%'] = adj_reb_chance
                else:
                    item = OrderedDict()
                    item['ID'] = player_stat.get('PLAYER_ID', 0)
                    item['Name'] = player_stat.get('PLAYER_NAME', '')
                    item['Nick Name'] = player_stat.get('NICKNAME', '')
                    item['TEAM_ID'] = player_stat.get('TEAM_ID', 0)
                    item['ADJ_DEF_REB_CHANCE_%'] = adj_reb_chance

                    item['GAME_TYPE'] = game_type
                    item['SEASON'] = year
                    item['DATE'] = f'01/01/{start_year}'

                    dict_key = f"{item['SEASON']}_{item['ID']}_{item['GAME_TYPE']}"
                    self.players_dict[dict_key] = item

                    # self.players_dict[item['ID']] = item

            except:
                a=1

        tracking_speed_distance_url = (
            f'https://stats.nba.com/stats/leaguedashptstats?College=&Conference=&Country=&DateFrom=&DateTo=&Division=&DraftPick=&'
            f'DraftYear=&GameScope=&Height=&ISTRound=&LastNGames=0&LeagueID=00&Location=&Month=0&OpponentTeamID=0&Outcome=&PORound=0&'
            f'PerMode=PerGame&PlayerExperience=&PlayerOrTeam=Player&PlayerPosition=&PtMeasureType=SpeedDistance&Season={year}'
            f'&SeasonSegment=&SeasonType=Playoffs&StarterBench=&TeamID=0&VsConference=&VsDivision=&Weight=')

        yield Request(url=tracking_speed_distance_url, callback=self.parse_speed_distance,
                      dont_filter=True, headers=self.json_headers, meta=response.meta)

    def parse_speed_distance(self, response):
        print('Tracking/Speed and Distance \n\n\n')
        year = response.meta.get('year')
        start_year = year.split('-')[0]
        game_type = response.meta.get('season_type', '')
        players_stats = self.get_players_stats(response)

        for player_stat in players_stats:
            try:
                player_id = player_stat.get('PLAYER_ID', 0.0)
                avg_speed = player_stat.get('AVG_SPEED_OFF', 0.0)

                player_key = f'{year}_{player_id}_{game_type}'
                if player_key in self.players_dict:
                    self.players_dict[player_key]['AVG_SPEED_OFF'] = avg_speed
                else:
                    item = OrderedDict()
                    item['ID'] = player_stat.get('PLAYER_ID', 0)
                    item['Name'] = player_stat.get('PLAYER_NAME', '')
                    item['Nick Name'] = player_stat.get('NICKNAME', '')
                    item['TEAM_ID'] = player_stat.get('TEAM_ID', 0)
                    item['AVG_SPEED_OFF'] = avg_speed

                    item['GAME_TYPE'] = game_type
                    item['SEASON'] = year
                    item['DATE'] = f'01/01/{start_year}'

                    dict_key = f"{item['SEASON']}_{item['ID']}_{item['GAME_TYPE']}"
                    self.players_dict[dict_key] = item
            except:
                a=1

        shooting_distance_zone_url = (
            f'https://stats.nba.com/stats/leaguedashplayershotlocations?College=&Conference=&Country=&DateFrom=&DateTo='
            f'&DistanceRange=By Zone&Division=&DraftPick=&DraftYear=&GameScope=&GameSegment=&Height=&ISTRound=&LastNGames=0&Location='
            f'&MeasureType=Base&Month=0&OpponentTeamID=0&Outcome=&PORound=0&PaceAdjust=N&PerMode=PerGame&Period=0&PlayerExperience='
            f'&PlayerPosition=&PlusMinus=N&Rank=N&Season={year}&SeasonSegment=&SeasonType=Pre Season&ShotClockRange=&StarterBench='
            f'&TeamID=0&VsConference=&VsDivision=&Weight=')

        yield Request(url=shooting_distance_zone_url, callback=self.parse_distance_zone,
                      dont_filter=True, headers=self.json_headers, meta=response.meta)

    def parse_distance_zone(self, response):
        print('Shooting/Distance Range==By Zone \n\n\n')
        year = response.meta.get('year')
        start_year = year.split('-')[0]
        game_type = response.meta.get('season_type', '')

        try:
            data_dict = response.json()
        except json.JSONDecodeError as e:
            data_dict = {}
            a = 1

        headers = [headers for headers in data_dict.get('resultSets', {}).get('headers', []) if
                   headers.get('name', '') == 'columns'][0].get('columnNames', [])
        records = data_dict.get('resultSets', {}).get('rowSet', [])

        players_stats = []

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

            players_stats.append(record_dict)

        for player_stats in players_stats:
            item = OrderedDict()
            item['FGM_RA'] = player_stats.get('FGM', 0.0)
            item['FGA_RA'] = player_stats.get('FGA', 0.0)
            item['FGM_PAINT'] = player_stats.get('FGM_1', 0.0)
            item['FGA_PAINT'] = player_stats.get('FGA_1', 0.0)
            item['FGM_MID-RANGE'] = player_stats.get('FGM_2', 0.0)
            item['FGA_MID-RANGE'] = player_stats.get('FGA_2', 0.0)
            item['FGM_CORNER'] = player_stats.get('FGM_7', 0.0)
            item['FGA_CORNER'] = player_stats.get('FGA_7', 0.0)
            item['FGM_AB'] = player_stats.get('FGM_5', 0.0)
            item['FGA_AB'] = player_stats.get('FGA_5', 0.0)

            player_id = player_stats.get('PLAYER_ID', 0.0)

            player_key = f'{year}_{player_id}_{game_type}'
            if player_key in self.players_dict:
                self.players_dict[player_key].update(item)

            else:
                item['ID'] = player_stats.get('PLAYER_ID', 0)
                item['Name'] = player_stats.get('PLAYER_NAME', '')
                item['Nick Name'] = player_stats.get('NICKNAME', '')
                item['TEAM_ID'] = player_stats.get('TEAM_ID', 0)
                item['TEAM_ABBREVIATION'] = player_stats.get('TEAM_ABBREVIATION', '')
                item['SEASON'] = year
                item['GAME_TYPE'] = game_type
                item['DATE'] = f'01/01/{start_year}'

                dict_key = f"{item['SEASON']}_{item['ID']}_{item['GAME_TYPE']}"
                self.players_dict[dict_key] = item

        hustle_url = (
            f'https://stats.nba.com/stats/leaguehustlestatsplayer?College=&Conference=&Country=&DateFrom=01/01/{start_year}&DateTo=12/31/{start_year}&'
            f'Division=&DraftPick=&DraftYear=&GameScope=&Height=&ISTRound=&LastNGames=0&LeagueID=00&Location=&Month=0&OpponentTeamID=0'
            f'&Outcome=&PORound=0&PaceAdjust=N&PerMode=PerGame&PlayerExperience=&PlayerPosition=&PlusMinus=N&Rank=N&Season={year}'
            f'&SeasonSegment=&SeasonType=Regular Season&TeamID=0&VsConference=&VsDivision=&Weight=')

        yield Request(url=hustle_url, callback=self.parse_hustle,
                      dont_filter=True, headers=self.json_headers, meta=response.meta)

    def parse_hustle(self, response):
        print('parse_hustle \n\n\n')
        year = response.meta.get('year')
        start_year = year.split('-')[0]
        game_type = response.meta.get('season_type', '')

        try:
            res_dict = response.json()
        except json.JSONDecodeError as e:
            res_dict = {}
            a = 1

        try:
            players_stats = res_dict.get('resultSets', [])[0].get('rowSet', [])
        except (IndexError, AttributeError):
            players_stats = []

        for player_stats in players_stats:
            try:
                deflections = player_stats[10]
                screen_ast_pt = player_stats[13]

                player_id = player_stats[0]

                player_key = f'{year}_{player_id}_{game_type}'
                if player_key in self.players_dict:
                    self.players_dict[player_key]['DEFLECTIONS'] = deflections
                    self.players_dict[player_key]['SCREEN_AST_PTS'] = screen_ast_pt

                else:
                    print('Player not exist')
            except:
                a=1

        shooting_efficiency_url = (
            f'https://stats.nba.com/stats/leaguedashptstats?College=&Conference=&Country=&DateFrom=&DateTo=&Division=&DraftPick='
            f'&DraftYear=&GameScope=&Height=&ISTRound=&LastNGames=0&LeagueID=00&Location=&Month=0&OpponentTeamID=0&Outcome=&PORound=0'
            f'&PerMode=PerGame&PlayerExperience=&PlayerOrTeam=Player&PlayerPosition=&PtMeasureType=Efficiency&Season={year}'
            f'&SeasonSegment=&SeasonType=Playoffs&StarterBench=&TeamID=0&VsConference=&VsDivision=&Weight=')

        yield Request(url=shooting_efficiency_url, callback=self.parse_shooting_efficiency,
                      dont_filter=True, headers=self.json_headers, meta=response.meta)

    def parse_shooting_efficiency(self, response):
        print('parse_shooting_efficiency \n\n\n')
        year = response.meta.get('year')
        game_type = response.meta.get('season_type', '')
        players_stats = self.get_players_stats(response)

        for player_stats in players_stats:
            item = OrderedDict()
            item['DRIVE_PTS'] = player_stats.get('DRIVE_PTS', 0.0)
            item['C&S_PTS'] = player_stats.get('CATCH_SHOOT_PTS', 0.0)
            item['PULL_UP_PTS'] = player_stats.get('PULL_UP_PTS', 0.0)
            item['PAINT_TOUCH_PTS'] = player_stats.get('PAINT_TOUCH_PTS', 0.0)
            item['POST_TOUCH_PTS'] = player_stats.get('POST_TOUCH_PTS', 0.0)
            item['ELBOW_TOUCH_PTS'] = player_stats.get('ELBOW_TOUCH_PTS', 0.0)

            player_id = player_stats.get('PLAYER_ID', 0.0)

            player_key = f'{year}_{player_id}_{game_type}'
            if player_key in self.players_dict:
                self.players_dict[player_key].update(item)

        defense_dash_2_points_url = (
            f'https://stats.nba.com/stats/leaguedashptdefend?College=&Conference=&Country=&DateFrom=&DateTo='
            f'&DefenseCategory=2 Pointers&Division=&DraftPick=&DraftYear=&GameSegment=&Height=&LastNGames=0'
            f'&LeagueID=00&Location=&Month=0&OpponentTeamID=0&Outcome=&PORound=0&PerMode=PerGame&Period=0'
            f'&PlayerExperience=&PlayerPosition=&Season={year}&SeasonSegment=&SeasonType=Playoffs&StarterBench='
            f'&TeamID=0&VsConference=&VsDivision=&Weight=')

        yield Request(url=defense_dash_2_points_url, callback=self.parse_defense_dash_2_points,
                      dont_filter=True, headers=self.json_headers, meta=response.meta)

    def parse_defense_dash_2_points(self, response):
        print('parse_defense_dash_2_points \n\n\n')
        year = response.meta.get('year')
        game_type = response.meta.get('season_type', '')
        players_stats = self.get_players_stats(response)

        for player_stats in players_stats:
            try:
                item = OrderedDict()

                fg = player_stats.get('FG2_PCT', 0.0)
                freq = player_stats.get('FREQ', 0.0)
                item['OPP_2PT_FREQ_%'] = freq * 100
                item['OPP_2PT_DFGM'] = player_stats.get('FG2M', 0.0)
                item['OPP_2PT_DFGA'] = player_stats.get('FG2A', 0.0)
                item['OPP_2PT_FG_%'] = fg * 100

                player_id = player_stats.get('CLOSE_DEF_PERSON_ID', 0)

                player_key = f'{year}_{player_id}_{game_type}'
                if player_key in self.players_dict:
                    self.players_dict[player_key].update(item)

                else:
                    print('Not matched records Dash 2')
            except:
                a=1

        defense_dash_3_points_url = (
            f'https://stats.nba.com/stats/leaguedashptdefend?College=&Conference=&Country=&DateFrom=&DateTo=&DefenseCategory=3 Pointers'
            f'&Division=&DraftPick=&DraftYear=&GameSegment=&Height=&LastNGames=0&LeagueID=00&Location=&Month=0&OpponentTeamID=0'
            f'&Outcome=&PORound=0&PerMode=PerGame&Period=0&PlayerExperience=&PlayerPosition=&Season={year}&SeasonSegment='
            f'&SeasonType=Playoffs&StarterBench=&TeamID=0&VsConference=&VsDivision=&Weight=')

        yield Request(url=defense_dash_3_points_url, callback=self.parse_defense_dash_3_points,
                      dont_filter=True, headers=self.json_headers, meta=response.meta)

    def parse_defense_dash_3_points(self, response):
        print('parse_defense_dash_3_points \n\n\n')
        year = response.meta.get('year')
        game_type = response.meta.get('season_type', '')
        players_stats = self.get_players_stats(response)

        for player_stats in players_stats:
            item = OrderedDict()

            freq = player_stats.get('FREQ', 0.0)
            fg = player_stats.get('FG3_PCT', 0.0)
            item['OPP_3PT_DFGA'] = player_stats.get('FG3A', 0.0)
            item['OPP_3PT_FREQ_%'] = freq * 100
            item['OPP_3PT_FG_%'] = fg * 100
            item['OPP_3PT_DFGM'] = player_stats.get('FG3M', 0.0)

            player_id = player_stats.get('CLOSE_DEF_PERSON_ID', 0)

            player_key = f'{year}_{player_id}_{game_type}'
            if player_key in self.players_dict:
                self.players_dict[player_key].update(item)

            else:
                print('Records NOt matched Dash 3 points')

        self.write_to_player_csv()

    def write_to_player_csv(self):
        folder_path = "PLAYER"
        os.makedirs(folder_path, exist_ok=True)

        # Iterate player data
        for player_id, player_record in self.players_dict.items():
            player_name = player_record.get('Name', '')
            player_nick_name = player_record.get('Nick Name', '').replace('.', ' ').replace("'", "")
            player_name_clean = player_name.replace('.', '').replace("'", "")

            filename = os.path.join(folder_path, f"{player_nick_name} {player_name_clean}.csv")

            # Check if the file exists to append or create a new one
            file_exists = os.path.isfile(filename)

            with open(filename, mode='a' if file_exists else 'w', newline='', encoding='utf-8') as csvfile:
                csv_writer = csv.DictWriter(csvfile, fieldnames=self.player_csv_headers)

                # Write headers if the file is new
                if not file_exists or csvfile.tell() == 0:
                    csv_writer.writeheader()

                # Write the player's data (ensure it's in the correct format)
                csv_writer.writerow(player_record)

                # self.logger.info(f"Saved data for {item.get('Name')} to {filename}")
                print(f"Saved data for {player_record.get('Name')} to {filename}")

        # CSV file to hold all player records
        combined_filename = os.path.join(folder_path, "2016.csv")

        # Check if the combined file exists to append or create a new one
        combined_file_exists = os.path.isfile(combined_filename)

        # Open the combined file in append mode or write mode if it doesn't exist
        with open(combined_filename, mode='a' if combined_file_exists else 'w', newline='',
                  encoding='utf-8') as combined_csvfile:
            combined_csv_writer = csv.DictWriter(combined_csvfile, fieldnames=self.player_csv_headers)

            # Write headers for the combined file if it doesn't exist or is empty
            if not combined_file_exists or combined_csvfile.tell() == 0:
                combined_csv_writer.writeheader()

            # Write each player's filtered data to the combined file
            for player_record in self.players_dict.values():
                filtered_record = {key: player_record.get(key, '') for key in self.player_csv_headers}
                combined_csv_writer.writerow(filtered_record)

            print(f"Saved all player data to {combined_filename}")

    def get_players_stats(self, response):
        # year = response.meta.get('year', '')
        # season_type = response.meta.get('season_type', '')
        # start_year = year.split('-')[0]

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
        players_stats = [dict(zip(headers, row)) for row in data_dict['rowSet']]

        if len(players_stats) == 0:
            a=1

        # return year, season_type, start_year, players_stats
        return players_stats or []

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(NbaPlayerSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_idle, signal=signals.spider_idle)
        return spider

    def spider_idle(self):
        self.players_dict = {}
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
