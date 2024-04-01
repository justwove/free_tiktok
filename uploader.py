from selenium import webdriver
from selenium.webdriver.common.by import By
from os import listdir
from chromedriver_autoinstaller import install as chromedriver_install
chromedriver_install()
from time import sleep
from random import randint, choice
from selenium_stealth import stealth
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from pathlib import Path

class Uploader:

    def __init__(self, platform: str | list, videos_path: str):
        self.platform = platform
        try:
            if videos_path.endswith('/'):
                self.videos = [f'{videos_path}{video}' for video in listdir(videos_path)]
            else:
                self.videos = [f'{videos_path}/{video}' for video in listdir(videos_path)]
        except:
            videos_path = Path(videos_path).mkdir(parents=True, exist_ok=True)
            if videos_path.endswith('/'):
                self.videos = [f'{videos_path}{video}' for video in listdir(videos_path)]
            else:
                self.videos = [f'{videos_path}/{video}' for video in listdir(videos_path)]

        self.videos_path = videos_path
        self.setup_selenium()

    def setup_selenium(self):
        options = webdriver.ChromeOptions()
        options.add_argument('--log-level=3')
        options.add_argument('user-data-dir=/mnt/c/Users/Seb/AppData/Local/Google/Chrome/User\ Data')
        options.add_argument('start-maximized')
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-extensions-file-access-check")
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        prefs = {'profile.managed_default_content_settings.images': 2, 'profile.managed_default_content_settings.video': 2}
        options.add_experimental_option('prefs', prefs)
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option("prefs", {"javascript.enabled": True})
        options.add_argument('--window-size=' + f"{randint(1024, 1920)}x{randint(768, 1080)}")
        options.add_argument('--force-timezone=' + choice(['US/Pacific', 'US/Mountain', 'US/Central', 'US/Eastern', 'Canada/Pacific', 'Canada/Mountain', 'Canada/Central', 'Canada/Eastern']))
        options.binary_location = '/usr/bin/google-chrome-stable'
        self.driver = webdriver.Chrome(options=options)
        stealth(
            self.driver,
            languages=[choice(["en-US", "en", "fr", "es", "de", "ja"])],
            vendor=choice(["Google Inc.", "Mozilla Foundation", "Microsoft Corporation", "Apple Inc.", "Samsung Electronics", "IBM Corporation", "Facebook, Inc.", "Amazon.com, Inc.", "Twitter, Inc.", "Intel Corporation", "Oracle Corporation", "Adobe Systems Incorporated", "Netflix, Inc.", "PayPal Holdings, Inc.", "Salesforce.com, Inc.", "Uber Technologies, Inc." ]),
            platform=choice(["Win32", "Linux x86_64", "Macintosh", "Android", "iOS", "Windows NT", "Ubuntu", "Fedora", "Chrome OS", "Raspbian", "FreeBSD", "OpenBSD", "Solaris", "PlayStation", "Xbox" ]),
            webgl_vendor=choice(["Intel Inc.", "NVIDIA Corporation", "AMD", "ARM", "Qualcomm", "Apple Inc.", "Broadcom", "Imagination Technologies", "Vivante Corporation", "Mali Technologies" ]),
            renderer=choice(["Intel Iris OpenGL Engine", "NVIDIA GeForce GTX", "AMD Radeon", "ARM Mali", "Qualcomm Adreno", "Apple A12 Bionic", "Broadcom VideoCore", "Imagination PowerVR", "Vivante GC Series", "Mali-G77", "Intel UHD Graphics", "AMD Radeon Pro", "NVIDIA Quadro" ])
        )

    ##############################################################################################
    ########################################TIKTOK################################################
    ##############################################################################################

    def tiktok_login(self):
        self.driver.find_element(By.XPATH, '//*[@id="loginContainer"]/div/div/div/div[3]/div[2]').click()
        sleep(1)
        self.driver.find_element(By.XPATH, '//*[@id="loginContainer"]/div[1]/form/div[1]/a').click()
        sleep(1)
        self.driver.find_element(By.XPATH, '//*[@id="loginContainer"]/div[1]/form/div[1]/a').send_keys('tiktok.setup184@passmail.net')
        self.driver.find_element(By.XPATH, '//*[@id="loginContainer"]/div[1]/form/div[2]/div/input').send_keys('Azerty*1234*')
        sleep(2)
        self.driver.find_element(By.XPATH, '//*[@id="loginContainer"]/div[1]/form/button').click()
        sleep(5)
        if '/creator-center/content' not in self.driver.current_url:
            input('Veuillez compléter le CAPTCHA')
        sleep(7)

    def tiktok_upload_video(self, video_path):
        sleep(2)
        self.driver.find_element(By.XPATH, '//*[@id="root"]/div[2]/div[2]/div/div/div/div[5]/button').click()
        sleep(1)
        self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[1]/div/div/div/div[1]/div/div/div[3]/div').send_keys(video_path)
        sleep(10)
        self.driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div/div[2]/div[2]/div[2]/div[7]/div[2]/button').click()

    def tiktok_upload(self):
        self.driver.get('https://www.tiktok.com/creator-center/content')
        sleep(2)
        if '/creator-center/content' not in self.driver.current_url:
            sleep(1)
            self.tiktok_login()
        
        [self.tiktok_upload_video(video_path) for video_path in self.videos_path]
        

    ##############################################################################################
    ########################################YOUTUBE###############################################
    ##############################################################################################

    def yt_downloader(self, shorts_urls):
        from pytube import YouTube
        for url in shorts_urls:
            youtube = YouTube(url, use_oauth=True, allow_oauth_cache=True)
            stream = youtube.streams.get_highest_resolution()
            if stream:
                video_title = stream.title
                print(f"Downloading ... [{url}] - [{video_title.strip()}]")
                stream.download(self.videos_path)

    def google_login(self):
        self.driver.get('https://github.com/') # better to do here random website function
        self.driver.implicitly_wait(time_to_wait=10)
        sleep(1)
        self.driver.execute_script('''window.open("https://www.google.com/intl/en/gmail/about/","_blank");''')
        self.driver.switch_to.window(self.driver.window_handles[0])
        self.driver.close()
        self.driver.implicitly_wait(time_to_wait=10)
        self.driver.switch_to.window(self.driver.window_handles[0])
        self.driver.implicitly_wait(time_to_wait=10)
        sleep(1)
        self.driver.find_element('xpath','//* [@data-action=\'sign in\']').click()
        self.driver.implicitly_wait(time_to_wait=10)
        self.driver.find_element('id','identifierId').send_keys('sgassackys')
        self.driver.find_element('id','identifierNext').click()
        self.driver.implicitly_wait(time_to_wait=10)

        wait = WebDriverWait(self.driver, 10)  # Maximum wait time of 10 seconds
        element = wait.until(EC.presence_of_element_located((By.NAME, "Passwd")))
        sleep(2)

        self.driver.find_element('name','Passwd').send_keys('Chernarus77390!*')
        self.driver.find_element('id','passwordNext').click()
        self.driver.implicitly_wait(time_to_wait=10)

    def ytb_upload_video(self, video_path):
        self.driver.get("https://studio.youtube.com")
        sleep(3)

        upload_button = self.driver.find_element(By.XPATH, '//*[@id="upload-icon"]')
        upload_button.click()
        sleep(1)

        file_input = self.driver.find_element(By.XPATH, '//*[@id="content"]/input')
        file_input.send_keys(video_path)
        sleep(10)

        next_button = self.driver.find_element(By.XPATH, '//*[@id="next-button"]')
        for i in range(3):
            next_button.click()
            sleep(1)

        done_button = self.driver.find_element(By.XPATH, '//*[@id="done-button"]')
        done_button.click()
        sleep(5)

    def youtube_upload(self):
        self.driver.get('https://studio.youtube.com')
        if 'https://studio.youtube.com' not in self.driver.current_url: 
            sleep(1)
            self.google_login()
            self.driver.get('https://studio.youtube.com')
        sleep(5)
        [self.ytb_upload_video(video_path) for video_path in self.videos_path]
            
if __name__ == '__main__': 
    upload = Uploader('', 'reddit_short/reddit_output/background')
    upload.yt_downloader([
        ''
    ])