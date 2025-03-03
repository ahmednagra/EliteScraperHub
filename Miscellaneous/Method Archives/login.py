import requests
from scrapy import Spider, Selector, Request
import json


class HeavytraderzSpider(Spider):
    name = "heavytraderz"
    start_urls = ["https://www.heavytraderz.live/livestream/"]

    headers = {
        'authority': 'www.heavytraderz.live',
        'accept': 'application/json, text/javascript, */*; q=0.01',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        # 'cookie': 'PHPSESSID=kqtfkr7q664sfslqrefjb4a2hg; _gcl_au=1.1.1154910707.1704534944; _gid=GA1.2.2047175217.1704534945; cookielawinfo-checkbox-necessary=yes; cookielawinfo-checkbox-non-necessary=no; __stripe_mid=ab934c93-5f54-4dd1-a3fd-539543d10b195be210; __stripe_sid=77d02a6e-127d-4ef2-bad5-516eb819eaa2ffcb66; CookieLawInfoConsent=eyJuZWNlc3NhcnkiOnRydWUsIm5vbi1uZWNlc3NhcnkiOmZhbHNlfQ==; viewed_cookie_policy=yes; wordpress_test_cookie=WP%20Cookie%20check; arm_cookie_24486=kqtfkr7q664sfslqrefjb4a2hg%7C%7C573751; _ga_CLD96KVCZF=GS1.1.1704534944.1.1.1704535582.7.0.0; _ga=GA1.2.395947828.1704534945',
        'origin': 'https://www.heavytraderz.live',
        'referer': 'https://www.heavytraderz.live/login-2/?restricted=page',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }
    data = {
        'action': 'arm_shortcode_form_ajax_action',
        'form_random_key': '106_qV4wfP6oAb',
        'user_login': 'Marcokr@gmx.de',
        'user_pass': 'kQ33bTaG8b8eqSW',
        'rememberme': 'forever',
        'arm_action': 'einloggen-3Rl',
        'redirect_to': 'https://www.heavytraderz.live',
        'isAdmin': '0',
        'referral_url': 'https://www.heavytraderz.live/livestream/',
    }
    headers_json = {
        'authority': 'www.heavytraderz.live',
        'accept': '*/*',
        'accept-language': 'en-PK,en;q=0.9,ur-PK;q=0.8,ur;q=0.7,en-US;q=0.6',
        'authorization': 'Bearer 7e5d97d42c664aa698d5428d02b4d9a4',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        # 'cookie': 'PHPSESSID=kqtfkr7q664sfslqrefjb4a2hg; _gcl_au=1.1.1154910707.1704534944; _gid=GA1.2.2047175217.1704534945; cookielawinfo-checkbox-necessary=yes; cookielawinfo-checkbox-non-necessary=no; __stripe_mid=ab934c93-5f54-4dd1-a3fd-539543d10b195be210; CookieLawInfoConsent=eyJuZWNlc3NhcnkiOnRydWUsIm5vbi1uZWNlc3NhcnkiOmZhbHNlfQ==; viewed_cookie_policy=yes; wordpress_test_cookie=WP%20Cookie%20check; htz-login-history-token=kqtfkr7q664sfslqrefjb4a2hg; arm_cookie_24486=kqtfkr7q664sfslqrefjb4a2hg%7C%7C573764; wordpress_logged_in_16387ff4434e6a8245dfd9a31d1ed01c=marcokr%40gmx.de%7C1705749226%7CJpwC2l1goYEOz7bLWjEJxOkew3S4BMsp9tc6EgUERFK%7C06068890f448be0d1a259191ace1272d7e32b7b4309c018066a53da839b720e6; _ga_CLD96KVCZF=GS1.1.1704538125.2.1.1704540139.49.0.0; _ga=GA1.1.395947828.1704534945',
        'origin': 'https://www.heavytraderz.live',
        'referer': 'https://www.heavytraderz.live/livetrades/',
        'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest',
    }

    def start_requests(self):
        url = 'https://www.heavytraderz.live/wp-admin/admin-ajax.php'
        session = requests.session()

        request = session.post(url, headers=self.headers, data=self.data)
        cookies = request.cookies.get_dict()

        yield Request(url=self.start_urls[0], cookies=cookies, callback=self.parse)

    def parse(self, response, **kwargs):
        team = response.css('.elementor-item:not([tabindex="-1"]) ::text').getall()
        team = [x.replace('Trader ', 'htz-').replace('Team ', 'htz-').replace(' ', '').lower() for x in team]

        url = 'https://www.heavytraderz.live/api/live-trades/all'
        data = {'traders[]': ['team'] + [f'{trader}' for trader in team[1:]], }

        res = requests.post(url=url, headers=self.headers_json, data=data)
        jason_data = res.json()
        a=1
