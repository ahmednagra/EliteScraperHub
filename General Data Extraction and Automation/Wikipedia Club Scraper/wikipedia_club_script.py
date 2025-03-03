import re
import os
import csv
import asyncio
from datetime import datetime
from urllib3.util import Retry
from urllib.parse import unquote

import aiohttp
import requests
import webcolors
import polars as pl
import xlwings as xw
from bs4 import BeautifulSoup
from geopy.geocoders import Nominatim
from requests.adapters import HTTPAdapter
from geopy.exc import GeocoderServiceError, GeocoderTimedOut


async def async_fetch_soup(req_url):
    session = requests.Session()
    retries = Retry(total=5, backoff_factor=1, status_forcelist=[502, 503, 504])
    session.mount('http://', HTTPAdapter(max_retries=retries))
    session.mount('https://', HTTPAdapter(max_retries=retries))

    try:
        # Extract language from URL
        match = re.search(r'//(.*)\.wikipedia', req_url)
        lang = match.group(1) if match else None

        if lang == 'en' or 'translate' in req_url:
            res = session.get(req_url)
            soup = BeautifulSoup(res.content, 'html.parser')
            return soup
        elif lang != 'en':
            url = f'https://translate.google.com/translate?sl=auto&tl=en&u={req_url}'
            url = url.replace(' ', '_')
            res = session.get(url)
            soup = BeautifulSoup(res.content, 'html.parser')

            if soup.title and 'Google Translate' == soup.title.text:
                print('Google could not translate it!')
            elif soup.title and 'Wikipedia' not in soup.title.text:
                print('Translation maybe went wrong:', soup.title.text)
            return soup
    except Exception as e:
        print(f"An error occurred for {req_url}: {e}")
        return ''


# CONVERTER DMS > DECIMAL
async def fn_dms2dec(degrees, minutes=0, seconds=0, direction='N'):
    decimal = degrees + minutes / 60 + float(seconds) / 3600
    if direction in 'SWO':  # 'O' is for 'West'
        decimal = -decimal
    return round(decimal, 4)


# "41º01'N 7º47'O",  "22°13'10.12\"S 49°56'21.86\"W", "22°13'10.12\"S 49°56'21.86\"W"
async def fn_dms_str_to_decimal(dms_str):
    # Define possible symbols for degrees, minutes, and seconds
    degree_symbols = r"º°d"
    minute_symbols = r"'’′m"
    second_symbols = r"\"”″s"

    # Define regex pattern to match DMS strings with and without seconds
    dms_pattern = re.compile(
        rf"(\d{{1,3}})[{degree_symbols}\s]*"
        rf"(\d{{1,2}})[{minute_symbols}\s]*"
        rf"(\d{{1,2}}(?:\.\d+)?)?[\s{second_symbols}]*"
        r"\s*([NSEOWL])")
    lat_match = dms_pattern.search(dms_str)
    lon_match = dms_pattern.search(dms_str[lat_match.end():])
    if not lat_match or not lon_match:
        raise ValueError("Invalid DMS coordinate format")

    def convert_match_to_decimal(match):
        deg = float(match.group(1))
        min = float(match.group(2))
        sec = float(match.group(3)) if match.group(3) else 0.0
        direction = match.group(4)
        decimal = deg + (min / 60) + (sec / 3600)
        if direction in 'SWO':  # Assume 'L' is West by default
            decimal = -decimal
        return decimal

    lat = round(convert_match_to_decimal(lat_match), 4)
    lon = round(convert_match_to_decimal(lon_match), 4)
    return lat, lon


# EXTRACTOR ##############################################################
# 1 id coordinates
async def fn_id_coordinates(soup):
    coordinates_span = soup.find('span', id='coordinates')
    if coordinates_span:
        try:
            coordinates_str = coordinates_span.find('span', class_='geo-dec').text
        except AttributeError:
            coordinates_str = coordinates_span.find('span', class_='geo-dms').text
        return coordinates_str
    else:
        return "no id-coordinates"


# 2  wgCoordinates - get DMS
async def fn_wgCoordinates(soup_str):
    pattern = re.compile(r'"wgCoordinates"\s*:\s*\{[^}]*\}', re.DOTALL)
    wgCoordinates = pattern.search(soup_str).group()
    wgCoordinates = wgCoordinates.replace('\n', '')
    return wgCoordinates


# 3 strCoordinates
async def fn_str_coordinates(soup_str):
    pattern = re.compile(r'"coordinates"\s*:\s*\[[^\]]+\]', re.DOTALL)
    coordinates = pattern.search(soup_str).group()
    coordinates = coordinates.replace('\n', '')
    return coordinates


# 4 geo_inline
async def fn_geo_inline(soup):
    coordinates_span = soup.find('span', class_='geo-inline')
    if coordinates_span:
        try:
            coordinates_str = coordinates_span.find('span', class_='geo-dec').text
            return coordinates_str

        except AttributeError:
            return "no geo_inline"


# 5 p-class
async def fn_external_text(soup):
    coordinates_p = soup.find('p', class_='coordinates')
    if coordinates_p:
        try:
            coordinates_str = coordinates_p.find('a', class_='external text').text
            return coordinates_str
        except AttributeError:
            return "external_text not found"
    else:
        return "no external text class"


# MAIN #################
async def fn_fetch_coordinates(soup):
    global flag_home
    lat = None
    lon = None
    soup_str = str(soup)
    # print("get coordinates")

    # 1 wgCoordinates in soup-string:
    # "wgCoordinates":{"lat":56.17159722222222,"lon":10.16303888888889}
    if "wgCoordinates" in soup_str:
        # 1 wgCoordinates - get DMS
        # if flag_home == True: print("FOUND: wgCoordinates")
        pattern = re.compile(r'wgCoordinates"\s*:\s*\{[^}]*\}', re.DOTALL)
        wgCoordinates = pattern.search(soup_str).group()
        wgCoordinates = wgCoordinates.replace('\n', '')
        lat_pattern = re.compile(r'"lat":(-?\d+\.?\d*)')
        lon_pattern = re.compile(r'"lon":(-?\d+\.?\d*)')
        lat = lat_pattern.search(wgCoordinates)
        lon = lon_pattern.search(wgCoordinates)
        if lat: lat = round(float(lat.group(1)), 4)
        if lon: lon = round(float(lon.group(1)), 4)
        return lat, lon

    # 3 COORDINATES in ID-Atribute
    # Formate: 11º 33' N, 104º 55' L
    elif soup.find(id="coordinates"):

        # if flag_home == True: print("FOUND id-coordinates")
        # lat,lon = fn_coordinates_in_id(soup)
        coordinates_div = soup.find('div', id='coordinates')
        if coordinates_div:
            coordinates_text = coordinates_div.find('a', class_='external text').text
            print("DMS_str in id coordinates:", coordinates_text)
            lat, lon = fn_dms_str_to_decimal(coordinates_text)
            return lat, lon

    # 2 coordinates in soup_str
    elif "coordinates" in soup_str:
        # if flag_home == True: print("FOUND: coordinates in soup_str")
        pattern = re.compile(r'"coordinates":\[(\-?\d+\.\d+),(\-?\d+\.\d+)\]', re.DOTALL)
        match = pattern.search(soup_str)
        if match:
            lat, lon = match.groups()
            lat = round(float(lat), 4)
            lon = round(float(lon), 4)
            return lat, lon

    # 4 COORDINATES in GEO-INLINE
    elif soup.find('span', class_='geo-inline'):
        if soup.find('span', class_='geo-inline'):
            if flag_home == True: print("coordinates in 'geo-inline'")
            try:
                # Find the span with class 'geo-inline'
                geo_inline_tag = soup.find('span', class_='geo-inline')
                # print(geo_inline_tag)
                if geo_inline_tag:
                    # Extract DMS coordinates if available
                    lat_tag = geo_inline_tag.find('span', class_='latitude')
                    lon_tag = geo_inline_tag.find('span', class_='longitude')
                    if lat_tag and lon_tag:
                        lat_text = lat_tag.get_text(strip=True)
                        lon_text = lon_tag.get_text(strip=True)
                        coordinates_str = f"{lat_text} {lon_text}"
                        lat, lon = fn_dms_str_to_decimal(coordinates_str)
            except Exception as e:
                lat = None
                lon = None
            return lat, lon

    # 5 p class = coordinates
    elif soup.find('p', class_='coordinates'):
        print("externalCoordinates")
        coordinates = await fn_external_text(soup)
        lat, lon = fn_dms_str_to_decimal(coordinates_str)
        return coordinates, lat, lon

    flag_home = False
    return lat, lon


async def fn_headline(soup):
    soup_str = str(soup)
    pattern = re.compile(r'"headline":"([^"]+)"')
    match = pattern.search(soup_str)
    if match:
        headline = match.group(1)
        headline = headline.encode('utf-8').decode('unicode_escape')
    else:
        headline = "no headline"
    return headline


async def extract_wikidata_urls(soup):
    soup_str = str(soup)
    pattern = re.compile(r'https://[^"]*\.wikidata\.org[^"]*')
    wikidata_urls = pattern.findall(soup_str)
    pattern = re.compile(r'^Q\d+$')
    for url in wikidata_urls:
        last_part = url.split("/")[-1]
        if pattern.match(last_part):
            q_number = last_part
            return q_number


async def fn_q_data(url):
    res = requests.get(url)
    soup = BeautifulSoup(res.content, 'html.parser')
    soup_str = str(soup)

    # Compile patterns for extracting Wikidata URLs and Q numbers
    wikidata_url_pattern = re.compile(r'https://[^"]*\.wikidata\.org[^"]*')
    q_number_pattern = re.compile(r'^Q\d+$')

    # Find all Wikidata URLs in the HTML
    wikidata_urls = wikidata_url_pattern.findall(soup_str)

    # Initialize variables
    fn_q_number = None
    api_fetcher = None
    q_api = None

    # Extract the q_number and corresponding description
    for url in wikidata_urls:
        last_part = url.split("/")[-1]
        if q_number_pattern.match(last_part):
            q_num = last_part

            if not fn_q_number:
                fn_q_number = q_num

            q_url = f'https://www.wikidata.org/w/api.php?action=wbgetentities&ids={q_num}&format=json&props=descriptions'
            res = requests.get(q_url)
            data = res.json()
            q_description = data['entities'][q_num]['descriptions'].get('en', {}).get('value',
                                                                                      'No description available')

            if not api_fetcher:
                api_fetcher = f'{q_num}, {q_description}'

            if not q_api:
                q_api = f'{q_num}, {q_description}'

    return fn_q_number, q_api, api_fetcher


async def get_country_from_coordinates(lat, lon):
    geolocator = Nominatim(user_agent="my_geopy_application")  # Use a descriptive user agent
    try:
        location = geolocator.reverse((lat, lon), exactly_one=True, language='en', timeout=10)
        if location:
            address = location.raw.get('address', {})
            country = address.get('country', '')
            return country
        else:
            return 'not found for coords'
    except (GeocoderTimedOut, GeocoderServiceError) as e:
        return f"Error: {str(e)}"


# fn_paragraph and loc
async def fn_fetch_loc(paragraph, base_url, soup):
    loc = loc_href = loc_coordinates = None

    paragraph_str = str(paragraph)

    # "in" oder "from" zuerst?
    if paragraph:
        para = paragraph.text.split(" ")
        try:
            index_in = para.index("in")
        except:
            index_in = 1000
        try:
            index_from = para.index("from")
        except:
            index_from = 1000
    # print("in", index_in, "from", index_from)

    # FROM
    if index_from < index_in:
        # print("fom-version", index_in, index_from)
        # version 1: from 20 a-tags
        for a in soup.find_all('a', href=True)[:20]:
            if 'from ' in a.get_text():
                loc = a.get("title")
                loc_href = a["href"]
                break
        # version 2: from paragraph-text
        if " from " in paragraph_str:
            from_text_parts = paragraph_str.split(" from ", 1)
            if len(from_text_parts) > 1:
                sib_str = from_text_parts[1]
                new_soup = BeautifulSoup(sib_str, "html.parser")
                for a_tag in new_soup.find_all("a", href=True):
                    try:
                        loc_href = a_tag["href"]
                        if loc_href.split("/")[1] == "wiki": loc_href = base_url + loc_href
                        loc = a_tag["title"]
                        loc = a_tag.text
                    except:
                        loc_href = None
                        loc = None
                    break
    # IN
    elif index_in < index_from:
        # print("in-version")
        # 1 check first 20 a-tags
        for a in paragraph.find_all('a', href=True)[:20]:
            text_lower = a.get_text().lower()
            # print(text_lower)
            if 'in ' in text_lower and "Football_in" not in a["href"]:
                # print("a-tagger", a.get_text())
                loc = a.get("title")
                loc_href = a["href"]
                break
        # 2 check paragraph-text
        in_text_parts = paragraph_str.split(" in ", 1)
        # print("'in' in paragraph", "str-version")
        if " in " in paragraph_str:
            if len(in_text_parts) > 1:
                sib_str = in_text_parts[1]
                new_soup = BeautifulSoup(sib_str, "html.parser")
                for a_tag in new_soup.find_all("a", href=True):
                    try:
                        loc_href = a_tag["href"]
                        if loc_href.split("/")[1] == "wiki": loc_href = base_url + loc_href
                        loc = a_tag["title"]
                        # print("URL loc href",loc_href)
                        break
                    except:
                        loc_href = None
                        loc = None
                        break
    else:
        print("Neither 'in' nor 'from' in first paragraph")

    if loc_href:
        if loc_href == "/wiki/Main_Page" or loc_href.startswith('/w/'):
            loc_href = None

    if loc and "main page" in loc.lower():
        loc = None

    return loc, loc_href


async def fn_fetch_paragraph(soup, url):
    soup_str = str(soup)
    # first find the paragraph
    club_url = url
    base_url = url.split("/wiki")[0]
    club_name = club_headline = club_q_number = description = loc_country = loc = loc_href = loc_lat = loc_lon = None

    # TITLE
    club_name = soup.title.string
    club_name = club_name.split(" - ")[0].strip()
    club_name = club_name.split(" – ")[0].strip()

    # HEADLINE
    pattern = re.compile(r'"headline":"([^"]+)"')
    match = pattern.search(soup_str)
    if match:
        headline = match.group(1)
        headline = headline.encode('utf-8').decode('unicode_escape')
        club_headline = headline

    # Q-NUMBER
    pattern = r'/Q\d+'
    match = re.search(pattern, soup_str)
    if match:
        club_q_number = match.group()[1:]

    # PARAGRAPH
    div = soup.find("div", id="mw-content-text")
    exclude_words = ["draft", "article", "knowledge", " see "]
    keywords = ["football", "soccer", "team", "club", "hometown"]
    paragraphs = div.find_all('p')
    for p in paragraphs:
        text = p.get_text().strip()
        # print("p text", text)
        text_lower = text.lower()
        if any(exclude_word in text_lower for exclude_word in exclude_words):
            # print("exclude word")
            continue

        # DESCRIPTION, LOC, LOC_HREF
        if any(keyword in text_lower for keyword in keywords):
            description = text.replace("\n", "").replace(" .", ".").replace(" ,", ",")
            # print(description)
            loc, loc_href = await fn_fetch_loc(p, base_url, soup)
            # print("LOC HREF",loc_href)
            if not loc_href:
                # print("NO loc_href from paragraph:",loc_href)
                loc = "No loc-info from paragraph"

            # COORDINATES
            if loc_href is not None:
                # print("LOC HREF",loc_href)
                response = requests.get(loc_href)
                soup_href = BeautifulSoup(response.content, 'html.parser')
                loc_lat, loc_lon = await fn_fetch_coordinates(soup_href)
            else:
                try:
                    url = 'https://www.wikidata.org/w/api.php'
                    params = {'action': 'wbgetentities', 'ids': club_q_number, 'format': 'json', 'props': 'claims'}
                    data = requests.get(url, params=params).json()
                    coords = data['entities'][club_q_number]['claims']['P625'][0]['mainsnak']['datavalue']['value']
                    loc_lat, loc_lon = coords['latitude'], coords['longitude']
                except:
                    if "Wikipedia" not in soup.title.text:
                        loc = "Potential Page Translation Problem"
                    pass
            # COUNTRY
            if loc_lat is not None and loc_lat != "need":
                # print("LOC LAT", loc_lat)
                loc_country = await get_country_from_coordinates(loc_lat, loc_lon)
            break
        else:
            # if flag_home: print("NO KEYWORD found in paragraph")
            description = "No keyword in paragraph"

    dict_page = {
        "club_q_number": club_q_number,
        "club_url": club_url,
        "club_name": club_name,
        "club_headline": club_headline,
        "club_description": description,
        "loc": loc,
        "loc_href": loc_href,
        "loc_lat": loc_lat,
        "loc_lon": loc_lon,
        "loc_country": loc_country}
    return dict_page


# fn_fetch_infobox_jerseys
# 'Home' and 'Away' in a single tr
async def fn_jerseys(soup):
    # global flag_home
    jersey_home = jersey_away = jersey_third = None
    # print("JERSEY SOUP ARRIVED", soup)
    jerseys = []
    infobox = soup.find(lambda tag: (tag.name == "table" or tag.name == "div") and tag.get("class") and (
            "infobox" in tag.get("class") or "toccolours" in tag.get("class")))

    def closest_colour(requested_colour):
        min_colours = {}
        try:
            for key, name in webcolors.CSS3_HEX_TO_NAMES.items():
                r_c, g_c, b_c = webcolors.hex_to_rgb(key)
                rd = (r_c - requested_colour[0]) ** 2
                gd = (g_c - requested_colour[1]) ** 2
                bd = (b_c - requested_colour[2]) ** 2
                min_colours[(rd + gd + bd)] = name
            return min_colours[min(min_colours.keys())]
        except:
            return min_colours

    def get_colour_name(requested_colour):
        try:
            closest_name = actual_name = webcolors.rgb_to_name(requested_colour)
        except ValueError:
            closest_name = closest_colour(requested_colour)
            actual_name = None
        return actual_name, closest_name

    if infobox:
        nested_table = infobox.find('table')

        if nested_table:
            for td in nested_table.find_all('td'):
                bg_colors = []
                background_colors = []
                # BG_COLORS
                if 'bgcolor' in td.attrs:
                    # print("bgcolor")
                    bg_colors.append(td['bgcolor'].strip())

                for nested_td in td.find_all('td'):
                    if 'bgcolor' in nested_td.attrs:
                        bg_colors.append(nested_td['bgcolor'].strip())

                # BACKGROUND COLORS
                divs = td.find_all('div', style=True)
                for div in divs:
                    styles = div['style'].split(';')
                    for style in styles:
                        if 'background-color' in style:
                            color = style.split(':')[1].strip()
                            background_colors.append(color)

                # the second bgcolor or background-color in td
                if len(bg_colors) >= 2:
                    hex_color = bg_colors[1]
                elif len(background_colors) >= 2:
                    hex_color = background_colors[1]
                    if hex_color == "#00000": hex_color = "#000000"
                    if hex_color == "#FFFFFFF": hex_color = "#FFFFFF"
                    # print("HEX", hex_color)
                else:
                    continue  # Skip if there are not enough colors

                # wenn hex_color "#" ist
                if hex_color == "#":
                    jerseys.append("#")

                # wenn hex_color echte hex-bezeichnung ist
                elif re.match(r'^#[0-9a-fA-F]{6}$', hex_color):
                    rgb_object = webcolors.hex_to_rgb(hex_color)
                    if rgb_object:
                        rgb = [rgb_object.red, rgb_object.green, rgb_object.blue]
                        actual, nearest = get_colour_name(rgb)
                        try:
                            actual = actual
                        except:
                            actual = ""
                        try:
                            nearest = nearest
                            jerseys.append(f"{nearest} {rgb}")
                            # print("Nearest", nearest, rgb)
                        except:
                            nearest = ""

                # wenn hex_color #colorword ist
                elif re.match(r'^#_?[a-z]+$', hex_color):
                    # print("colorword", hex_color)
                    jerseys.append(f"{hex_color[1:]}")

                else:
                    print(hex_color, "is no hexmatch")
                    jerseys.append("no match")
                hex_color = ""

            try:
                jersey_home = jerseys[0]
            except:
                jersey_home = None
            try:
                jersey_away = jerseys[1]
            except:
                jersey_away = None
            try:
                jersey_third = jerseys[2]
            except:
                jersey_third = None

    return jersey_home, jersey_away, jersey_third


# fn_fetch_infobox
async def fn_fetch_infobox(soup):
    soup_str = str(soup)
    infobox = soup.find(lambda tag: (tag.name == "table" or tag.name == "div") and tag.get("class") and (
            "infobox" in tag.get("class") or "toccolours" in tag.get("class")))

    capacity_names = ["capacity", "seating capacity", "places", "ability"]
    full_names = ["full name", "name", 'full name of the club', "full title", "long name", "title"]
    no_gos = ["page does not exist", "not yet drafted", "page not found", "page not available", "not written yet"]
    name_flag = False
    full_name = None
    nickname = None
    short_name = None
    stadium_capacity = None
    colors = None

    for nr, tr in enumerate(infobox.find_all('tr')):
        if len(tr.find_all(['td', 'th'], recursive=False)) != 2: continue

        # first tag in row:
        first_tag = tr.find(['td', 'th'], recursive=False)
        if not first_tag: continue
        last_td = tr.find_all('td')[-1]

        # CAPACITY
        for capacity_name in capacity_names:
            if capacity_name.lower() in tr.get_text(strip=True).lower():
                stadium_capacity = last_td.get_text(strip=True).replace(",", "")
                stadium_capacity = re.sub(r'\[.*?\]', '', stadium_capacity)
                stadium_capacity = re.sub(r'\(.*?\)', '', stadium_capacity)
                stadium_capacity = re.sub(r'[^\d]', '', stadium_capacity)

        # FULL NAME
        if name_flag == False:
            if any(full_name.lower() in first_tag.get_text(strip=True).lower() for full_name in full_names):
                full_name = last_td.get_text(strip=True)
                name_flag = True

        # NICK NAME
        if "nick" in first_tag.get_text(strip=True).lower():
            parts = []
            for tag in last_td.find_all(['i', 'li', 'a', 'br']):
                text = tag.get_text(strip=True)
                if text:
                    text = re.sub(r'\[\d+\]', '', text)
                    text = text.replace("citation needed", "")
                    parts.append(text)
            nickname = ', '.join(parts)
            nickname = re.sub(r',\s*,', ', ', nickname).strip(', ')

        # SHORT NAME
        if "short" in first_tag.get_text(strip=True).lower():
            # print("short")
            parts = []
            td_text = last_td.get_text(strip=True)
            if td_text:
                parts.append(re.sub(r'\[\d+\]', '', td_text))

            # text von anderen tags
            for tag in last_td.find_all(['i', 'li', 'a', 'br']):
                text = tag.get_text(strip=True)
                if text:
                    text = re.sub(r'\[\d+\]', '', text)
                    parts.append(text)
            short_name = ', '.join(parts)
            short_name = re.sub(r',\s*,', ', ', short_name).strip(', ')

        # COLOR
        if "color" in first_tag.get_text(strip=True).lower():
            parts = []
            for tag in last_td.find_all(['i', 'li', 'a', 'br']):
                text = tag.get_text(strip=True)
                if text:
                    text = re.sub(r'\[\d+\]', '', text)
                    parts.append(text)
            colors = ', '.join(parts)
            colors = re.sub(r',\s*,', ', ', colors).strip(', ')

    # JERSEY
    home_jersey, away_jersey, third_jersey = await fn_jerseys(soup)

    dict_infobox = {
        "info_full_name": full_name,
        "info_nickname": nickname,
        "info_short_name": short_name,
        "info_stadium_capacity": stadium_capacity,
        "info_colors": colors,
        "info_home_jersey": home_jersey,
        "info_away_jersey": away_jersey,
        "info_third_jersey": third_jersey
    }

    return dict_infobox


# fn_fetch_stadium ###################
a_tags_matching = 0
stadium_names = ["stadium", "stadion", "estade", "name of the stadium", "ground", "home field", "venue",
                 "football field", "arena", "home arena", "home track", "complex", "home court", "pitch"]

no_gos = ["page does not exist", "not yet drafted", "page not found", "page not available", "not written yet"]


async def fn_headline_and_q(stadium_url):
    headline = q_number = q_description = ""
    async with aiohttp.ClientSession() as session:
        async with session.get(stadium_url) as response:
            if response.status == 200:
                stadium_html = await response.text()
                stadium_soup = BeautifulSoup(stadium_html, 'html.parser')
                stadium_soup_str = str(stadium_soup)

                # 1 HEADLINE
                pattern = re.compile(r'"headline":"([^"]+)"')
                match = pattern.search(stadium_soup_str)
                if match:
                    headline = match.group(1)
                    headline = headline.encode('utf-8').decode('unicode_escape')
                else:
                    headline = "no headline"

                # 2 Q-NUMBER and DESCRIPTION
                pattern = re.compile(r'https://[^"]*\.wikidata\.org[^"]*')
                wikidata_urls = pattern.findall(stadium_soup_str)
                pattern = re.compile(r'^Q\d+$')
                for url in wikidata_urls:
                    last_part = url.split("/")[-1]
                    if pattern.match(last_part):
                        q_number = last_part
                        # get description from wikidata
                        q_url = f'https://www.wikidata.org/w/api.php?action=wbgetentities&ids={q_number}&format=json&props=descriptions'

                        async with aiohttp.ClientSession() as session:
                            async with session.get(q_url) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    q_description = data['entities'][q_number]['descriptions'].get('en', {}).get('value',
                                                                                                     'No description available')
                        break
                print("HEAD Q", headline, q_number, q_description)
                return headline, q_number, q_description


async def count_matching_a_tags(td_tag):
    count = 0
    for a_tag in td_tag.find_all('a'):
        text = a_tag.get_text(strip=True)
        title = a_tag.get('title')
        # Check if the title attribute exists and if the title matches the text
        if title and text == title:
            count += 1
    return count


async def fn_fetch_stadium(soup, base_url):
    soup_str = str(soup)
    infobox = soup.find(lambda tag: (tag.name == "table" or tag.name == "div") and tag.get("class") and (
            "infobox" in tag.get("class") or "toccolours" in tag.get("class")))

    stadium_list = []

    dict_stadium = {key: None for key in
                    ["stadium_a_tag_count", "stadium_br_tag_count", "stadium_a_tags_matching", "stadium_lat",
                     "stadium_lon", "stadium_country"]}

    dict_stadium.update({
        "stadium_a_text": "",
        "stadium_a_title": "",
        "stadium_a_href": "",
        "stadium_headline": "",
        "stadium_q_number": "",
        "stadium_q_description": ""
    })

    a_infos = []
    url_trans = None
    stadium_flag = False
    coordinates_flag = False

    for tr in infobox.find_all('tr'):
        # print(nr)
        if len(tr.find_all(['td', 'th'], recursive=False)) != 2: continue

        # first tag in row:
        first_tag = tr.find(['td', 'th'], recursive=False)
        if not first_tag: continue
        last_td = tr.find_all('td')[-1]

        if any(stadium_name.lower() in tr.get_text(strip=True).lower() for stadium_name in stadium_names):
            stadium_flag = True

            # basic about a-tag
            stadium_a_tag_count = len(last_td.find_all('a'))
            stadium_a_tags_matching = await count_matching_a_tags(last_td)
            stadium_br_tag_count = len(last_td.find_all('br'))
            dict_stadium["stadium_a_tag_count"] = stadium_a_tag_count
            dict_stadium["stadium_br_tag_count"] = stadium_br_tag_count
            dict_stadium["stadium_a_tags_matching"] = stadium_a_tags_matching

            # url_trans auf None
            if url_trans: url_trans = None

            # td_text
            td_text = str(last_td)
            td_text = re.sub(r'<.*?>', '  ', td_text).strip()  # remove html-tags
            td_text = td_text.replace("  ", ",")  # separate by ", "
            td_text = re.sub(r',\s*\d+\s*,', ',', td_text)  # remove number between commas
            td_text = re.sub(r'\s*,\s*,\s*', ', ', td_text)  # remove multiple commas
            td_text = re.sub(r'\s*,+\s*', ', ', td_text)  # remove multiple commas
            td_text = re.sub(r' \s*,+', '', td_text)  # remove multiple commas
            td_text = re.sub(r'\s*,+\s*', ', ', td_text)  # remove comma/whitespace
            td_text = re.sub(r'\[.*?\]', '', td_text)  # remove square brackets
            stadium_list.append(td_text)

            if stadium_a_tag_count > 0:
                headline = q_number = q_description = ""
                lat = lon = country = ""

                # a-tags in a_infos
                for element in last_td.find_all('a'):
                    a_text = element.get_text(strip=True)
                    if a_text == "": a_text = "no text"
                    if "translate" in element["href"] or "http" in element["href"]:
                        a_href = element['href']
                    else:
                        a_href = base_url + element['href']
                    a_title = element.get('title', '')
                    if a_title == "": a_title = "not title"

                    if "index" in a_href or "File:" in a_href or "geohack" in a_href or any(
                            no_go.lower() in a_title.lower() for no_go in no_gos):
                        a_title = "no title"
                        a_href = "no url"
                    elif "translate" in a_href or "wikipedia" in a_href:
                        headline, q_number, q_description = await fn_headline_and_q(a_href)
                        if coordinates_flag == False:
                            async with aiohttp.ClientSession() as session:
                                async with session.get(a_href) as response:
                                    a_tag_html = await response.text()
                                    a_tag_soup = BeautifulSoup(a_tag_html, 'html.parser')
                                    lat, lon = await fn_fetch_coordinates(a_tag_soup)
                                    # COUNTRY
                                    if lat:
                                        coordinates_flag = True
                                        country = await get_country_from_coordinates(lat, lon)
                                    else:
                                        country = "unknown"
                        else:
                            lat = lon = country = ""

                    print("a_text:", a_text, "a_href:", a_href, "a_title:", a_title, ",country:", country, ",lat", lat,
                          ",lon", lon)

                    if dict_stadium["stadium_a_text"]: dict_stadium["stadium_a_text"] += ", "
                    dict_stadium["stadium_a_text"] += a_text

                    if dict_stadium["stadium_a_title"]: dict_stadium["stadium_a_title"] += ", "
                    dict_stadium["stadium_a_title"] += a_title

                    if dict_stadium["stadium_a_href"]: dict_stadium["stadium_a_href"] += ", "
                    dict_stadium["stadium_a_href"] += unquote(a_href)

                    if dict_stadium["stadium_headline"]: dict_stadium["stadium_headline"] += ", "
                    dict_stadium["stadium_headline"] += headline

                    if dict_stadium["stadium_q_number"]: dict_stadium["stadium_q_number"] += ", "
                    dict_stadium["stadium_q_number"] += q_number

                    if dict_stadium["stadium_q_description"]: dict_stadium["stadium_q_description"] += ", "
                    dict_stadium["stadium_q_description"] += q_description

                    dict_stadium["stadium_lat"] = lat
                    dict_stadium["stadium_lon"] = lon
                    dict_stadium["stadium_country"] = country

            a_tags_matching = 0

    # print(stadium_list)
    dict_stadium["stadium_text"] = ', '.join(stadium_list)
    if stadium_flag == False:
        dict_stadium["notice"] = "no stadium"

    return dict_stadium

# fn_fetch_infobox_founded############


async def convert_date(date_str):
    pattern1 = r'(\d{1,2}) (\w+) (\d{4})'  # For "29 June 1945"
    pattern2 = r'(\w+) (\d{1,2})\s*,\s*(\d{4})'  # For "December 10, 2021"
    pattern3 = r'(\d{2})/(\d{2})/(\d{4})'  # For "24/04/1956"
    match1 = re.match(pattern1, date_str)
    match2 = re.match(pattern2, date_str)
    match3 = re.match(pattern3, date_str)

    if match1:
        day, month, year = match1.groups()
        date_obj = datetime.strptime(f"{day} {month} {year}", "%d %B %Y")
        return date_obj.strftime("%Y-%m-%d")
    elif match2:
        month, day, year = match2.groups()
        date_obj = datetime.strptime(f"{month} {day} {year}", "%B %d %Y")
        return date_obj.strftime("%Y-%m-%d")
    elif match3:
        day, month, year = match3.groups()
        date_obj = datetime.strptime(f"{day}/{month}/{year}", "%d/%m/%Y")
        return date_obj.strftime("%Y-%m-%d")
    else:
        return "founding date problem"


# FOUNDED
founded_terms = [
    "Founded", "Foundation", "Established", "Formation", "Inception", "Created",
    "Began", "Started", "Commenced", "Institution", "Constituted",
    "Incorporated", "Initiated", "Set up", "Launched", "Birth", "Founded as",
    "Began as", "Created as", "Founded in", "Started in", "Established in",
    "Organized in", "Formed in", "Instituted in", "Constituted in",
    "Incorporated in", "Initiated in", "Originated in", "Established on",
    "Founded on", "Organized on", "Formed on", "Instituted on", "Constituted on",
    "Incorporated on", "Initiated on", "Originated on", "Founding date",
    "Date of establishment", "Date of founding", "Date of creation",
    "Date of inception", "Date of commencement", "Date of origin",
    "Date started", "Year founded", "Year established", "year of establishment", "Year of foundation",
    "Year of creation", "Year of inception", "Year of commencement",
    "Year of origin", "Year started", "Originated from", "Created from",
    "Started from", "Established from", "Founded from", "Incepted from",
    "Launched from", "Date of launch", "Launch date", "Year of launch",
    "Originally founded", "Originally established", "Originally created",
    "Originally started", "Initially founded", "Initially established",
    "Initially created", "Initially started", "Initially commenced",
    "Initially organized", "Originally organized", "Formation date",
    "Year of formation", "Formation year", "Commencement date",
    "Year of commencement", "Year of institution", "Institutional date",
    "Year of constitution", "Constitutional date", "Year of incorporation",
    "Incorporation date", "Year of initiation", "Initiation date",
    "Year of origin", "Original date", "Origin year", "Establishment year",
    "Establishment date", "Historical founding", "Historical establishment",
    "Historical creation", "Historical inception", "Historical commencement",
    "Year of foundation", "Founding", "Founded in", "Establishment",
    "Establish", "Set up", "Creation", "Creation date", "Stand", "Formed",
    "Beginning", "Based", "Fundamentally"
]

td_text = None
founded = None


async def fn_founded(soup):
    soup_str = str(soup)
    infobox = soup.find(lambda tag: (tag.name == "table" or tag.name == "div") and tag.get("class") and (
                "infobox" in tag.get("class") or "toccolours" in tag.get("class")))

    founded = None
    for tr in infobox.find_all('tr'):
        if len(tr.find_all(['td', 'th'], recursive=False)) != 2: continue
        first_tag = tr.find(['td', 'th'], recursive=False)
        if not first_tag: continue
        last_td = tr.find_all('td')[-1]
        if any(founded_term.lower() in first_tag.get_text(strip=True).lower() for founded_term in founded_terms):
            td_text = last_td.get_text(separator=" ").strip()

            td_text = last_td.get_text(separator=' ').strip().replace('\n', '')
            td_text = re.sub(r'\s+', ' ', td_text)  # remove dirty commas
            td_text = re.sub(r'\[.*?\]', '', td_text)  # remove square brackets
            td_text = re.sub(r'\[.*?years.*?\]', '', td_text)  # remove (... years ago)
            td_text = re.sub(r'\(.*?years.*?\)', '', td_text)  # remove (..years)

            td_text = re.sub(r'\([^()]*\bas\b[^()]*\)', "", td_text)  # remove (as ...)
            td_text = await convert_date(td_text)
            founded = td_text.split(";")[0]
            break
    return founded


# SAVE
def save_to_csv(df):
    if len(df) > 0:
        clubs = "wikipedia_clubs.csv"
        if os.path.exists(clubs):
            with open(clubs, newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                headers = reader.fieldnames
                dtype_dict = {col: pl.Utf8 for col in headers}
                df_wikipedia_clubs = pl.read_csv(clubs, dtypes=dtype_dict)

                df_wikipedia_clubs = df_wikipedia_clubs.with_columns(
                    [pl.col(column).cast(pl.Utf8) for column in df_wikipedia_clubs.columns])

                df_wikipedia_clubs = df_wikipedia_clubs.vstack(df)
                df_wikipedia_clubs = df_wikipedia_clubs.unique(subset=["club_q_number"], maintain_order=True)
                df_wikipedia_clubs = df_wikipedia_clubs.with_columns(pl.col("nr").cast(pl.Int32)).sort("nr")
                df_wikipedia_clubs.write_csv(clubs)
        else:
            df.write_csv(clubs)


async def get_done_urls(clubs):
    done_urls = []
    data = []
    if os.path.exists(clubs):
        with open(clubs, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            for row in reader:
                data.append(dict(row))
        done_urls.extend([url.get('club_url', '') for url in data])
        return done_urls, headers
    else:
        return done_urls, ''


async def process_url(nr, url, done_urls, dict_page_template):
    try:
        url = url.strip()
        if url in done_urls:
            return None  # Skip if URL is already processed

        print('\n', nr, url)
        base_url = url.split("/wiki")[0]
        dict_page = dict_page_template.copy()

        soup = await async_fetch_soup(url)
        if soup:
            if soup.title.text == "Google Translate":
                dict_page["nr"] = nr
                dict_page["club_url"] = url
                dict_page["notice"] = "Google could not translate"
                return dict_page

        soup_str = str(soup)
        infobox = soup.find(lambda tag: (tag.name == "table" or tag.name == "div") and tag.get("class") and (
                "infobox" in tag.get("class") or "toccolours" in tag.get("class")))

        if infobox:
            # Process infobox, stadium info, etc.
            dict_stadium = await fn_fetch_stadium(soup, base_url)
            founded = await fn_founded(soup)
            dict_infobox = await fn_fetch_infobox(soup)
        else:
            dict_page["notice"] = "no infobox"
            print(nr, url, "no infobox")
            dict_infobox = {}
            dict_stadium = {}
            founded = ""

        dict_paragraph = await fn_fetch_paragraph(soup, url)
        dict_page.update(dict_paragraph)
        dict_page.update(dict_stadium)
        dict_page.update(dict_infobox)
        dict_page["founded"] = founded
        dict_page["nr"] = nr

        return dict_page

    except Exception as e:
        print(f"An error occurred for {url}: {e}")
        return None


async def main():
    print('\n# LOOP')

    # DONE urls
    clubs = "wikipedia_clubs.csv"
    done_urls, headers = await get_done_urls(clubs)

    # MAKE URLS
    urls = []
    df_urls = pl.read_csv("wd_clubs.csv")
    for url in df_urls["url"]:
        urls.append(url)

    # DICTIONARY TEMPLATE
    keys = ['nr', 'club_q_number', 'club_url', 'club_name', 'club_headline', 'loc_country', 'loc', 'loc_lat', 'loc_lon',
            'stadium_q_number', 'stadium_text', 'stadium_q_description', 'stadium_a_text', 'stadium_a_title',
            'stadium_country', 'stadium_headline', 'stadium_lat', 'stadium_lon', 'info_stadium_capacity', 'info_colors',
            'info_home_jersey', 'info_away_jersey', 'info_third_jersey', 'founded', 'info_full_name', 'info_nickname',
            'info_short_name', 'club_description', 'loc_href', 'stadium_a_href', 'stadium_a_tag_count',
            'stadium_br_tag_count', 'stadium_a_tags_matching', 'notice']
    dict_page_template = {key: None for key in keys}

    df = pl.DataFrame()
    # frow = 690
    # lrow = 2000

    frow = 1
    lrow = 1000

    # Define batch size and semaphore
    batch_size = 5
    semaphore = asyncio.Semaphore(batch_size)

    tasks = []
    for nr in range(frow, lrow):
        # Wait for the semaphore before starting a new task
        await semaphore.acquire()
        task = asyncio.create_task(process_url(nr, urls[nr], done_urls, dict_page_template))
        task.add_done_callback(lambda t: semaphore.release())  # Release semaphore after task is done
        tasks.append(task)

        # If we've reached the batch size or finished all URLs, await current batch of tasks
        if len(tasks) == batch_size or nr == len(urls) - 1:
            results = await asyncio.gather(*tasks)
            tasks = []  # Clear tasks list for the next batch

            # Process results and accumulate in DataFrame
            df = pl.DataFrame()
            for result in results:
                if result:
                    df_page = pl.DataFrame(result)
                    df_page = df_page.with_columns([pl.col(column).cast(pl.Utf8) for column in df_page.columns])
                    df = pl.concat([df, df_page], how="vertical")

            # Save the batch to CSV if not empty
            if len(df) > 0:
                save_to_csv(df)

    # Final save of any remaining data
    if len(df) > 0:
        save_to_csv(df)
    #                 # Save to CSV (modify save_to_csv function for asynchronous handling if necessary)
    #                 if int(result["nr"]) % 10 == 0:
    #                     save_to_csv(df)
    #
    # if len(df) == 0:
    #     print("no new data")
    # else:
    #     save_to_csv(df)
    pdf = df.to_pandas()
    xw.view(pdf)

    # Print columns for verification
    print(df.columns)

    cols = ['nr', 'club_q_number', 'club_url', 'club_name', 'club_headline', 'loc_country', 'loc', 'loc_lat',
            'loc_lon', 'stadium_q_number', 'stadium_text', 'stadium_q_description', 'stadium_headline',
            'stadium_a_text', 'stadium_a_title', 'stadium_country', 'stadium_lat', 'stadium_lon',
            'info_stadium_capacity', 'info_colors', 'info_home_jersey', 'info_away_jersey', 'info_third_jersey',
            'founded', 'info_full_name', 'info_nickname', 'info_short_name', 'club_description', 'loc_href',
            'stadium_a_href', 'stadium_a_tag_count', 'stadium_br_tag_count', 'stadium_a_tags_matching', 'notice']
    df = df.select(cols)
    df = pl.read_csv("wikipedia_clubs.csv")
    headers = headers if headers else cols
    dtype_dict = {col: pl.Utf8 for col in headers}
    df_wikipedia_clubs = pl.read_csv(clubs, dtypes=dtype_dict)


if __name__ == '__main__':
    asyncio.run(main())
