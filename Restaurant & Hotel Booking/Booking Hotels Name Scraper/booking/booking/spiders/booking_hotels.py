import json
from urllib.parse import urlparse, parse_qs

from scrapy import Spider, Request

try:
    from nocowanie_hotels import process_csv_file, write_to_excel
except ImportError:
    from .nocowanie_hotels import process_csv_file, write_to_excel


class HotelsNamesSpider(Spider):
    name = "booking_hotels"

    headers = {
        'authority': 'www.booking.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'cache-control': 'max-age=0',
        # 'cookie': 'px_init=0; cors_js=1; bkng_sso_session=e30; OptanonConsent=implicitConsentCountry=nonGDPR&implicitConsentDate=1687183249390; _gid=GA1.2.739013668.1687183260; pcm_consent=consentedAt%3D2023-06-19T14%3A01%3A00.837Z%26countryCode%3DPK%26expiresAt%3D2023-12-16T14%3A01%3A00.837Z%26implicit%3Dfalse%26regionCode%3DPB%26regulation%3Dnone%26legacyRegulation%3Dnone%26consentId%3D0fc2e171-92ad-460e-a2fb-ff441510b240%26analytical%3Dtrue%26marketing%3Dtrue; bkng_sso_auth=CAIQsOnuTRqEAYNoEJ7X2BPfWXFKXv2IqQzYGKuFZXJJyrZg0Oo8cCncYUbQivzaAqwB6tT0pgP3kRzqeUtmIjSguQPTa4RVPWIkRrQQR6HNSZEHG47G++Bmr49rvG7uPmbbPJzAkmWDMMIbfGDds656GFshBRcMEhRGbH9dJs/qAN4luPNRVs6OTkNo+w==; bkng_sso_auth_1687183260=CAIQsOnuTRqEAYNoEJ7X2BPfWXFKXv2IqQzYGKuFZXJJyrZg0Oo8cCncYUbQivzaAqwB6tT0pgP3kRzqeUtmIjSguQPTa4RVPWIkRrQQR6HNSZEHG47G++Bmr49rvG7uPmbbPJzAkmWDMMIbfGDds656GFshBRcMEhRGbH9dJs/qAN4luPNRVs6OTkNo+w==; BJS=-; bkng_sso_ses=eyJib29raW5nX2dsb2JhbCI6W3siYSI6MSwiaCI6IlFIdjNmZXFYZFVCczRnWWNhRmVKcUhUUHJ4bGJsN1NtZ29FS3hZMm5HRFUifV19; _pxhd=bSHK5fDqSAahpOlQQfbfJX3EpBfxoOn%2F7-VQ0NR34Bxpo6JQoYoLdVZErQ3egVZWoJLyPNALvDzblje7Ra9H1w%3D%3D%3AVUKf4nKXusd%2Ff3ESUWG4FCbEioLB9kUFz8-K2WXA6fNEU3J6GQtSK4VlkvY1KzasJLxjy5T8AjiUCKmNYi-o%2FPaT7-oNTkVXW355u-4XXCg%3D; pxcts=df6fbd35-0ea9-11ee-869c-764246726174; _pxvid=d46ae0e8-0ea9-11ee-81cc-caacede7899f; _gcl_au=1.1.770503325.1687183350; bkng_prue=1; _scid=a62d0c26-8461-4dad-8f1d-5f75cc55e330; _pin_unauth=dWlkPU1UQmhaRFZqTVdJdE5tUTFZUzAwTkdaaExXRm1PVFl0WWpCaE9EQmpNek5sWXpoaw; _sctr=1%7C1687114800000; g_state={"i_p":1687190773783,"i_l":1}; reese84=3:zfzuyI+oLA3m/2PRCL/obg==:01pWLx4MXIQyhNok6iwj1dOKgt0E6+8ZLDeLqePps7z/YfSelyOKX2pjvdCZo4kxwarLkiEIXSnxVwis0NhJzaq+/FJu+exVCLn5MzzN4S296UoWbPHf8YfS+OYRseSfjWHpRzusyPCAOaYG140b6Uu1xK10M96LCnruQeRODvojNDsF9Zy0bmGwtbZV9vU3APF5yblCd1jq65U1oxamPx+ALCSEoP0liPIrZYRrZJW+abgGExoBSPdcku4pmPkj/NaHRS5ItPXMgFL1XrCCq3tBMbXkBoY61mcifK/bhdbPC9iCpbxLG+1+CZxEN5YLReOuuzjWP8eMSu2ppz561Ax44VVkEtrDiX25WFhj9FV7YHufJx+aQWUi3wL6fDM4j8s1ndyV0K9Y9Jct6yi7ZeKEehG/ZNGToau5oWcxigPujoiDAcj0hVOb0yqQAdQZKH9qZ9/OXqIkyYAekYF3FA==:QKdYeZnKkUyP1CRo/AiWE0zErz4S2umxt/rfKFYUYbo=; _gat=1; _pxff_cfp=1; _pxff_ddtc=1; _px3=3c321a94c60ca2852bb2ef1174f0ad56904f6f6dbf28db4b01206ee9c3041292:nDJz6OfPln9FxwCO0zYLpNieeGroyi9SS5svFqLJo/kIGq8d6kjxwQZg7fGw3E8OU7w5ioppdGhAMJpJfKab2g==:1000:/I/UkCphoqtRrVoKzSXVxu3k2Di1OSSJLZx8lhamYnTAhSWLwVozMVjey+KDNwqJrEF1Z1mlca7Jncm7UlQvxk1ItNyrn/VZnmalroiA4TvzZ8lp61hyZRGu5USqf8W26+zaHzktKvVNuASbCA+xBwKj4dG+ZT3AsT4d4IyubqWzj5DG/Xg593cvbC4SHAi/fYe6vWXw7G6dOc65HQBCEA==; _pxde=b922bfe85eb2507d0dbbb9591c79e7d48bd4c52c45fce606191ac0b0d34b4f6d:eyJ0aW1lc3RhbXAiOjE2ODcxODk3MjAxNDEsImZfa2IiOjAsImlwY19pZCI6W119; _scid_r=a62d0c26-8461-4dad-8f1d-5f75cc55e330; _ga=GA1.1.530824279.1687183260; _ga_FPD6YLJCJ7=GS1.1.1687188674.2.1.1687189720.0.0.0; _uetsid=0f21c5600eaa11eebf8ea32de7c222d8; _uetvid=0f22c5e00eaa11eea803cb9ea8a06f30; bkng=11UmFuZG9tSVYkc2RlIyh9Yaa29%2F3xUOLbnmKTRaewPBvEGbt3s36DFSPphqorJmJlQ8cbEL5bX3bWbYIHRccNW8CsHQFnwj%2Bzzm0G2IKGAd4mR529Uutb2W%2Fqu5PK4U42IktgRMbwI0cee8ZqDVDNJLPlCHqQTRybRDhtXqk9WUueF0NW0ZndMRYbjRwksW392T0dpeYd7ro%3D; lastSeen=0',
        'sec-ch-ua': '"Not.A/Brand";v="8", "Chromium";v="114", "Google Chrome";v="114"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'none',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
    }

    cookies = {
        'px_init': '0',
        'cors_js': '1',
        'bkng_sso_session': 'e30',
        'OptanonConsent': 'implicitConsentCountry=nonGDPR&implicitConsentDate=1687183249390',
        '_gid': 'GA1.2.739013668.1687183260',
        'BJS': '-',
        '_pxvid': 'd46ae0e8-0ea9-11ee-81cc-caacede7899f',
        '_gcl_au': '1.1.770503325.1687183350',
        '_scid': 'a62d0c26-8461-4dad-8f1d-5f75cc55e330',
        '_pin_unauth': 'dWlkPU1UQmhaRFZqTVdJdE5tUTFZUzAwTkdaaExXRm1PVFl0WWpCaE9EQmpNek5sWXpoaw',
        '_sctr': '1%7C1687114800000',
        'bkng_sso_ses': 'eyJib29raW5nX2dsb2JhbCI6W3siYSI6MSwiaCI6IlV1V3MwZXVSbm05OHdERWFDNmhSR2FsRk1TVGp3RFg2dkw4NUJVOC9jVFEifV19',
        'pcm_consent': 'consentedAt%3D2023-06-20T01%3A19%3A10.959Z%26countryCode%3DPK%26expiresAt%3D2023-12-17T01%3A19%3A10.959Z%26implicit%3Dfalse%26regionCode%3DPB%26regulation%3Dnone%26legacyRegulation%3Dnone%26consentId%3D0fc2e171-92ad-460e-a2fb-ff441510b240%26analytical%3Dtrue%26marketing%3Dtrue',
        'bkng_sso_auth': 'CAIQsOnuTRqEAeRPA0Y9A9qsY8sd685r3ZmmrhzOtwwbZHQDHYyO+GlsL4aCMf0WouFbx1/Gg+NnHLn5ANFalSE/0Uh/0wO0eadY1aYvEdCi6kxrIIZpF4ZR3holnvdoP6rf+warE4stfoliGdpZ5dHzf+wcdrLWpOArcLPxzFS9F2jLUV2cL2+uU8O5Ng==',
        'bkng_sso_auth_1687223950': 'CAIQsOnuTRqEAeRPA0Y9A9qsY8sd685r3ZmmrhzOtwwbZHQDHYyO+GlsL4aCMf0WouFbx1/Gg+NnHLn5ANFalSE/0Uh/0wO0eadY1aYvEdCi6kxrIIZpF4ZR3holnvdoP6rf+warE4stfoliGdpZ5dHzf+wcdrLWpOArcLPxzFS9F2jLUV2cL2+uU8O5Ng==',
        '_pxhd': 'fUzxnGog1Eto9My-CSQBabJIbrJG2sfdQWTM9Yb0Npk9vzsKmWeSxxvMTcF6QeaN0t6K8Ku7doUTUqKFKJMs0A%3D%3D%3AFIVT4gkBRcHFrInHzsqDKYDp9uOp8BApqXhQvDcGrH3wqrJzex8IAR1WMIUqrj-COX514DWe6F9zOVd6HJhY7nk4Ri%2FQOMZ8LH5RATp4T9Q%3D',
        'pxcts': '7ea0e7e5-0f08-11ee-a4a7-525857494868',
        'bkng_prue': '1',
        'reese84': '3:DTIvQtdZsYI0DWjeMKUcXA==:yj7rNL6FGmKJrj4OEXfRLCVeg/luMUWS4qFNsCSdbQiCJ0WhlqS2bbOzpuhaNUWpeUgUrL/z+HBp2yNcBnFXYbShOXqA3Ww1O6QvIYCcQ+Z0FvtD7xcV7N9HJRTMrCIPpWfITEf5ojJXLHl6MxojQO4Y/Vyw6uYwLg7egmcZjM5GB0vBy+/Kp4NIqOGlRLvTOyFG8aG1TvUG84OMH+9FrBp1Q6pi6TBAthUSxAWbQGL1x7T+K0hbWww3nAM+IPzl+n1TBKXRGf5V/IZj5ycgQ8Jx3w/Lzdo9+fhU+T3coa+LXfYOmftLLbyfsEuQjqvaP/6ewai9csMj91s6VuVAj4It4xQjA9D4yLFCvL4gsdlqS85FE+abopZDX+A0x36BOAcDpV46fMt8io5aMGcDC+GkZi1koTSYmKc+LpzY11rxnX1nDedN8c2Km8pwg2OmfM87uECOq+Chb9lG6YQNmw==:POTHKOs/6iiIN5XqxPIIZfmavLfn4w2iCdKOfj2HMx0=',
        'g_state': '{"i_p":1687310389612,"i_l":2}',
        '_pxff_cfp': '1',
        '_pxff_ddtc': '1',
        '_px3': '28dfac76009f5414445e973a2964e5a17887a2a34e8d3d49ca4a93fc481261e4:gl3LmIh28jzqDs1pHKED6RPeyOYN2Tmiw0R6N5MWzFgIk6ICLXbuwlelAWFp99tYiUBx/avdA5M4xnft7U8XDg==:1000:B/iZMXv0qDiCx15u2VgtVSI3r7kz+vCaLiiIrD1gt8GHTYeQ+IgW0xH9SBTmPfM+7zmr2VnddpjiOy8+E/kBPcEOXXXcohIZp5svMrTgw3s2yF8AlDmCEaCj0bOIyKC6L2KdaeFE0zHIGkYqRdxySUaeGoRQdkufIJje4s2BnCTEauHHMTer281EEqWHsppQyAf4u9Sv1mVICkTUuvOoww==',
        '_pxde': 'ca2e724af70f4ff8e217c98a978f74dfe1422516e26828864c66be27778edf19:eyJ0aW1lc3RhbXAiOjE2ODcyMjQwOTc2NDgsImZfa2IiOjAsImlwY19pZCI6W119',
        '_scid_r': 'a62d0c26-8461-4dad-8f1d-5f75cc55e330',
        '_ga': 'GA1.1.530824279.1687183260',
        '_uetsid': '0f21c5600eaa11eebf8ea32de7c222d8',
        '_uetvid': '0f22c5e00eaa11eea803cb9ea8a06f30',
        'bkng': '11UmFuZG9tSVYkc2RlIyh9YXjA6rtNF48dyfPzTHjBgvvQVXg9QQ686ZnrQZ%2Fs1Lkq7XeDDN3%2BlB8lX4hGula0WmlpRw3Ku7NVMdxLrhNv7SnGh%2BWdAekMRfi1n27rD6pnn9DPeia2Wrd1b2psc6ebyhHwyWw%2FIc5S0hJ2C740TIeG64MaMF5psdCp9QOS3qmfBwHaUGe56Es%3D',
        '_ga_FPD6YLJCJ7': 'GS1.1.1687223969.3.1.1687224104.0.0.0',
        'lastSeen': '0',
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.city_urls = [row['booking'] for row in process_csv_file()]

    def start_requests(self):
        for url in self.city_urls:
            yield Request(url=url,
                          headers=self.headers,
                          cookies=self.cookies,
                          callback=self.parse)

    def parse(self, response):
        url_params = parse_qs(urlparse(response.url).query)

        try:
            json_data = json.loads(response.css('[data-capla-store-data="apollo"]::text').get(''))
            data = json_data.get("ROOT_QUERY", {}).get("searchQueries", {})
            records = [(key, value) for key, value in data.items()][1][1]['results']
        except (json.JSONDecodeError, AttributeError, IndexError, KeyError):
            records = []

        data = []
        for record in records:
            Hotel_Name = record.get('displayName', {}).get('text', '') or ''
            price = record.get('priceDisplayInfo', {})
            Disc_Price = price.get('displayPrice', {}).get('amountPerStay', {}).get('amountRounded', '') \
                                    .replace('zł', '').strip().replace(' ', '') or ''
            try:
                Discounted_Price = float(Disc_Price)
            except ValueError:
                Discounted_Price = ''
            Act_Price = price.get('priceBeforeDiscount', {}).get('amountPerStay', {}) \
                                .get('amountRounded', '').replace('zł', '').strip().replace(' ', '') or ''
            try:
                Actual_Price = float(Act_Price)
            except ValueError:
                Actual_Price = ''

            City_Name = record.get('location', {}).get('displayLocation', {})
            if not City_Name:
                url_params.get('ss', '')
            if not City_Name:
                url_params.get('ssne', '')

            Date_start = url_params.get('checkin', '')
            if not Date_start:
                Date_start = url_params.get('checkin_year', [''])[0] + '-' + \
                             url_params.get('checkin_month', [''])[0] + '-' + \
                             url_params.get('checkin_monthday', [''])[0]

            Date_end = url_params.get('checkout', '')
            if not Date_end:
                Date_end = url_params.get('checkout_year', [''])[0] + '-' + \
                           url_params.get('checkout_month', [''])[0] + '-' + \
                           url_params.get('checkout_monthday', [''])[0]

            Guests_adult = url_params.get('group_adults', '')
            Guest_children = url_params.get('group_children', '')

            # Append the data to the list
            data.append([Hotel_Name, Actual_Price, Discounted_Price, Date_start, Date_end,
                         Guests_adult, Guest_children, City_Name])

        sheet_name = 'booking_hotels'
        write_to_excel(data, sheet_name)

        current_url = response.url
        if 'offset=' in current_url:
            pass
        else:
            updated_url = current_url + '&offset=25'
            yield Request(url=updated_url, headers=self.headers,
                          cookies=self.cookies,
                          callback=self.parse)
