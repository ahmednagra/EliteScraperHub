from threading import Thread
from datetime import datetime
import os, glob, json, logging, time

from scrapy import Request, Spider, Selector

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class PsychologySpider(Spider):
    name = "Psychology"
    current_dt = datetime.now().strftime("%d%m%Y%H%M")
    start_urls = ["https://www.psychologytoday.com/us/therapists"]

    custom_settings = {
        'CONCURRENT_REQUESTS': 4,
    }

    headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36',
        }

    def __init__(self):
        super().__init__()
        self.new_profile_count = 0
        self.mail_send_count = 0
        self.profile_urls = []
        self.email_sending_active = True  # Flag to stop email sending when needed

        # Create directories for logs and output
        os.makedirs("output", exist_ok=True)

        # Logs
        self.mail_sent_filepath = f'output/mail_sent.txt'
        self.profiles_urls_filepath = f'output/profiles_urls.txt'
        self.previous_sent_mails = self.read_previous_send_mails(self.mail_sent_filepath)
        self.previous_profile_urls = self.read_previous_send_mails(self.profiles_urls_filepath)
        self.profile_urls.extend(self.previous_profile_urls)

        # Browser Chrome & Start Selenium in a separate thread
        self.driver = webdriver.Chrome()
        chrome_options = Options()
        chrome_options.add_argument("--incognito")  # Enables incognito mode
        self.email_thread = Thread(target=self.process_emails, daemon=True)
        self.email_thread.start()  # Starts processing emails in a separate thread

    def start_requests(self):
        yield Request(url=self.start_urls[0], headers=self.headers, callback=self.parse, meta={'handle_httpstatus_all':True})

    def parse(self, response, **kwargs):
        if response.status !=200:
            print('Facing Blocking so Script is closed and end mails from previous written profile urls txt file')
            return

        states_urls = response.css('.suggestion-columns .suggestion-link::attr(href) ').getall()[:54]

        for state_url in states_urls:
            yield Request(url=state_url, headers=self.headers, callback=self.parse_states)

    def parse_states(self, response):
        try:
            data_dict = json.loads(response.css('#__NUXT_DATA__ ::text').get())
        except json.JSONDecodeError as e:
            return

        try:
            data = str(data_dict)
            city_part = data.split('ProfResults.CityHeading')[1].split('ProfResults.SubregionHeading')[0].split(',')
            cities_urls = [url for url in city_part if 'https://www.psychologytoday.com/us/therapists' in url]

            for city_url in cities_urls:
                city_url = city_url.strip().replace("'", '')
                yield Request(url=city_url, headers=self.headers, callback=self.parse_city)

        except Exception as e:
            print('Face Error in States Function')

    def parse_city(self, response):
        dr_urls = response.css('.results-row.top-divider .results-row-image::attr(href)').getall()

        for url in dr_urls:
            if url not in self.profile_urls:
                self.new_profile_count+= 1
                self.profile_urls.append(url)
            else:
                a=1

            if url not in self.previous_profile_urls:
                self.write_urls(url, key='profile_url')

        next_page = response.css('.pagination-controls-end a::attr(href)').get('')
        if next_page:
            yield Request(url=next_page, headers=self.headers, callback=self.parse_city)

    def process_emails(self, key=None):
        """Continuously process URLs in `self.profile_urls` and send emails one by one."""
        while self.email_sending_active or self.profile_urls:
            if self.profile_urls:
                url = self.profile_urls.pop(0)  # Get the first URL from the list
                if url in self.previous_sent_mails:
                    continue

                self.send_email(url)
            else:
                time.sleep(5)  # Wait if no URLs are available

    def send_email(self, url):
        try:
            # Open the URL
            self.driver.get(url)
            wait = WebDriverWait(self.driver, 10)  # Wait up to 10 seconds

            # Wait for the email button
            buttons = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".lets-connect-email-button button")))

            if len(buttons) >= 2:  # Ensure at least two elements are found
                second_button = buttons[1]  # Get the second button
                wait.until(EC.element_to_be_clickable(second_button)).click()  # Wait and click
                logging.info(f"Opened email form for: {url}")

                # Fill out the form
                name = 'Lauren Howard'
                email= 'lauren@lbeegroups.com'
                phone = '561-730-2457'
                subject = 'Therapy Resources'
                # message = 'We provide peer support groups for $20 and Autism/ADHD assessments for $485 in all 50 states. Think this could be helpful for your patients?'
                message = ('Hello! \n\n We realized when trying to find tools for our own patients that adult autism assessments were hard to find and often difficult to afford.'
                           ' \n\n At LBee Health, we developed an accessible and more-affordable adult autism evaluation. You can find out more at our website at lbeehealth.com/adultautism. If we can ever be of assistance to your patients, please let us know. You can join our referral program, which guarantees expedited services, at lbeehealth.com/referralpartners.'
                           '\n\nIf I can answer any questions, I would be happy to. Thank you!')

                wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "#name")))
                self.driver.find_element(By.CSS_SELECTOR, "#name").send_keys(name)  # YOUR NAME
                self.driver.find_element(By.CSS_SELECTOR, "#email").send_keys(email)  # Email
                self.driver.find_element(By.CSS_SELECTOR, "#phone").send_keys(phone)  # PHONE
                self.driver.find_element(By.CSS_SELECTOR, "#subject").send_keys(subject)  # SUBJECT
                self.driver.find_element(By.CSS_SELECTOR, "#body").send_keys(message) # Message

                html= Selector(text=self.driver.page_source)

                # Check the checkbox
                already_selected = html.css("a.checkbox-container span.selected").get('')
                if not already_selected:
                    checkbox = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.checkbox-container")))
                    checkbox.click()

                time.sleep(2)
                # ✅ Wait for the button
                send_email_button = wait.until(
                    EC.presence_of_element_located((By.XPATH, '//button[normalize-space()="Send Email"]'))
                )

                # ✅ Move the cursor to the button and click it
                actions = ActionChains(self.driver)
                actions.move_to_element(send_email_button).click().perform()

                time.sleep(5)
                print("Form submitted successfully.")

                try:
                    # Wait for the success message to appear (max 10 seconds)
                    success_message = WebDriverWait(self.driver, 50).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.success-message")))

                    # Verify if the success message contains the expected text
                    if "Success! Your message is on its way." in success_message.text:
                        self.mail_send_count += 1

                        # Write successful mail profile URLs in the txt file
                        self.write_urls(url, key='mail_sent')
                        print("✅ Email sent successfully!")
                        time.sleep(2)
                    else:
                        print("⚠️ Success message detected, but text did not match.")

                except Exception as e:
                    print("❌ Success message did not appear within 10 seconds:", str(e))

        except Exception as e:
            print("Error:", e)

    def write_urls(self, url, key):
        file_path = ''
        if key=='mail_sent':
            file_path = self.mail_sent_filepath
        elif key=='profile_url':
            file_path = self.profiles_urls_filepath

        with open(file_path, mode='a', encoding='utf-8') as logs_file:
            logs_file.write(f'{url}\n')

    def read_previous_send_mails(self, file_path):
        file = glob.glob(file_path)[0]
        try:
            with open(file, mode='r') as txt_file:
                return [line.strip() for line in txt_file.readlines() if line.strip()]

        except FileNotFoundError:
            print(f"File not found: {file}")
            return []
        except Exception as e:
            print(f"An error occurred: {str(e)}")
            return []

    def close(spider, reason):

        """Shutdown logic when the spider closes."""
        spider.email_sending_active = False  # Stop the email thread
        spider.email_thread.join()  # Ensure all emails are processed
        spider.driver.quit()
        logging.info(f"Total New Profile URLs Found: {spider.new_profile_count}")
        logging.info(f"Total Profiles MAil Send Successfully : {spider.mail_send_count}")
