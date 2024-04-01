from os import getenv, listdir, remove
from sys import path
from random import randint, choice
from elevenlabs_api import voice_over

from praw import Reddit
from praw.models import MoreComments 
from time import sleep, time
from re import sub as re_sub
from random import randint

from moviepy.editor import AudioFileClip, VideoFileClip, ImageClip, concatenate_videoclips, CompositeVideoClip

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium_stealth import stealth
from chromedriver_autoinstaller import install as chromedriver_install
chromedriver_install()

class Reddit_short:

    def __init__(self, client_id: str, client_secret: str, user_agent: str, subreddit: str) -> None:
        self.reddit_session: Reddit = Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        with open('reddit_output/used_ids.txt', 'r') as used_reddit_ids: 
            self.used_reddit_ids: list[str] = used_reddit_ids.readlines() 

        with open('.env', 'r') as env_file: env_file=env_file.readlines()
        self.keys: dict[str] = {
            'ELEVENLABS_API_KEY': env_file[0].split('=')[1]
        }
        self.subreddit = subreddit
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

    def get_posts(self, max_post: int=50):
        posts = [
            post for post in self.reddit_session.subreddit(self.subreddit).top(time_filter="day", limit=max_post) \
            if post.id not in self.used_reddit_ids
        ]
        posts_ids = [post.id for post in posts]
        with open('reddit_output/used_ids.txt', 'a') as used_reddit_ids:
            used_reddit_ids.write('\n'.join(posts_ids))
            used_reddit_ids.write('\n')
        
        self.used_reddit_ids = posts_ids
        self.posts = posts

    def get_content_from_posts(self):
        self.posts_content = {
            post.id: {
                'Title': post.title,
                'Comments': [(comment.body, comment.id) for comment in post.comments[:75] if (type(comment) != MoreComments and len(comment.body) > 150)],
                'URL': post.url
            }
        for post in self.posts}
        for index, post_id in enumerate(self.posts_content.keys()):
            title_voice_over = (AudioFileClip(voice_over(
                f'voice_over/{post_id}.wav', self.posts_content[post_id]['Title'] # //*[@id="t3_{post_id}"]
            )), post_id)

            comments_voice_over = [
                (AudioFileClip(voice_over(
                    f'voice_over/{comment_id}.wav', comment                         # //*[@id="t1_{comment_id}-comment-rtjson-content"]
            )), comment_id) for comment, comment_id in self.posts_content[post_id]['Comments']]

            # Faire take_screenshot()
            self.current_voice_over = (title_voice_over, comments_voice_over)
            self.post_url = self.posts_content[post_id]['URL']
            self.take_screenshot()
            self.prepare_shorts()

            title_clip = ImageClip(
                f"reddit_output/Screenshots/{title_voice_over[1]}.png",
                duration=title_voice_over[0].duration
            ).set_position(('center', 'center'))
            title_clip = title_clip.resize(width=(width-64))
            title_clip = title_clip.set_audio(title_voice_over[0])
            title_clip.fps = 1

            

            for audio_id_list in self.clips:
                clip = []
                for i, audio, id in enumerate(audio_id_list):
                    if i == 0: clip.append(title_clip); continue
                    video_background = VideoFileClip(
                        filename=f"reddit_output/background/shorts/{choice(listdir('reddit_output/background/shorts'))}",
                        audio=False
                    )
                    width, _ = video_background.size
                    comment_clip = ImageClip(
                        f"reddit_output/Screenshots/{id}.png",
                        duration=audio.duration
                    ).set_position(('center', 'center'))
                    comment_clip = comment_clip.resize(width=(width-64))
                    comment_clip = comment_clip.set_audio(audio)
                    comment_clip.fps = 1
                    clip.append(comment_clip)
                
                content_clips = concatenate_videoclips(clip).set_position(("center", "center"))
                final_clip = CompositeVideoClip(
                    clips=[video_background, content_clips],
                    size=video_background.size
                ).set_audio(content_clips.audio)
                final_clip.duration = sum([_clip.duration for _clip in clip])
                final_clip.set_fps(video_background.fps)
                print(f'Rendering video {self.posts_content[post_id]["Title"]}')
                final_clip.write_videofile(
                    f'reddit_output/shorts_upload/{self.posts_content[post_id]["Title"]}_{index}.mp4', 
                    codec='mpeg4',
                    threads='16', 
                    bitrate='8000k'
                )


            video_background = VideoFileClip(
                filename=f"reddit_output/background/{choice(listdir('reddit_output/background/shorts'))}",
                audio=False
            )
            width, _ = video_background.size
            clip = []
            clip.append(title_clip)
            for comment in comments_voice_over:
                comment_clip = ImageClip(
                    f"reddit_output/Screenshots/{comment[1]}.png",
                    duration=comment[0].duration
                ).set_position(('center', 'center'))
                comment_clip = comment_clip.resize(width=(width-64))
                comment_clip = comment_clip.set_audio(comment[0])
                comment_clip.fps = 1
                clip.append(comment_clip)

            content_clips = concatenate_videoclips(clip).set_position(("center", "center"))
            final_clip = CompositeVideoClip(
                clips=[video_background, content_clips],
                size=video_background.size
            ).set_audio(content_clips.audio)
            final_clip.duration = sum([_clip.duration for _clip in clip])
            final_clip.set_fps(video_background.fps)
            print(f'Rendering video {self.posts_content[post_id]["Title"]}')
            final_clip.write_videofile(
                f'reddit_output/video_upload/{self.posts_content[post_id]["Title"]}.mp4', 
                codec='mpeg4',
                threads='16', 
                bitrate='8000k'
            )

            self.post_ids = [comment_id for _, comment_id in self.posts_content[post_id]['Comments']]
            self.post_ids.append(post_id)
            [remove(f'voice_over/{_id}.wav') for _id in self.post_ids]
            [remove(f'reddit_output/screenshots/{_id}.png') for _id in self.post_ids]

    def take_screenshot(self):
        self.driver.get(self.post_url)
        sleep(2)
        title = (self.current_voice_over[0][1], self.driver.find_element(By.XPATH, f'//*[@id="t3_{self.current_voice_over[0][1]}"]').screenshot_as_png)
        comments = [(comment[1], self.driver.find_element(By.XPATH, f'//*[@id="t1_{comment[1]}-comment-rtjson-content"]').screenshot_as_png) for comment in self.current_voice_over[1]]

        with open(f'reddit_output/Screenshots/{title[0]}.png', 'wb') as screenshot_title:
            screenshot_title.write(title[1])

        for comment in comments:
            with open(f'reddit_output/Screenshots/{comment[0]}.png', 'wb') as screenshot_comment:
                screenshot_comment.write(comment[1])
    
    def prepare_shorts(self):
        default_duration = self.current_voice_over[0][0].duration
        duration = default_duration
        self.clips = []
        clip = [self.current_voice_over[0][0]]
        for comment in self.current_voice_over[1]:
            if duration + comment[0].duration > 60: 
                self.clips.append(clip)
                clip = []
                duration = default_duration

            if clip == []: clip.append(self.current_voice_over[0])
            duration += comment[0].duration
            clip.append(comment)


if __name__ == '__main__':
    reddit = Reddit_short(client_id='DImzTXoLORVX5GYysZKj7A', client_secret='-y5qoVYKz1xIPXta7BanudwCrMlrgQ', user_agent='Reddit bot', subreddit='AskReddit')
    reddit.get_posts()
    print(reddit.posts)
    print()
    reddit.get_content_from_posts()
    print()
    print(reddit.posts_content)
