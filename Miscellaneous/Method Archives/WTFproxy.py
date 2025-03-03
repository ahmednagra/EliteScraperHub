import requests


# Function to generate a random string
import random
import string


def generate_random_string(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))
user = "leadersfire---gmail.com"
password = "aEgL_SrEB1wXSnwUO7yvQ"
total_requests_to_do = 25
requests_for_new_ip = 10

ip_check_url = 'https://httpbin.org/ip'

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'}

for count in range(1, total_requests_to_do + 1):
    if count % requests_for_new_ip == 0:
        sessionId = generate_random_string()
        proxy = {
            'http': f'http://{user}:{password}_session-{sessionId}@proxy.wtfproxy.com:3030',
            'https': f'http://{user}:{password}_session-{sessionId}@proxy.wtfproxy.com:3030'}
        
        try:
            response = requests.get(ip_check_url, proxies=proxy, headers=headers, timeout=10)
            if response.status_code == 200:
                ip = response.json().get('origin', 'No IP found')
                print(f"Proxy changed. IP is {ip}")
            else:
                print(f"Failed to get IP with proxy. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error occurred while using proxy: {e}")
    else:
        try:
            response = requests.get('https://google.com', headers=headers, timeout=10)
            if response.status_code != 200:
                print(f"Request failed. Status code: {response.status_code}")
        except Exception as e:
            print(f"Error occurred during request: {e}")

    print(f"Request {count} completed.")
