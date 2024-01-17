from os import getenv, listdir
from sys import path
from elevenlabs_api import voice_over

from dotenv import load_dotenv
from praw import Reddit
from time import sleep, time
from markdown import markdown
from re import sub as re_sub
from bs4 import BeautifulSoup
from random import randint

from moviepy.editor import AudioFileClip, VideoFileClip, ImageClip, concatenate_videoclips, CompositeVideoClip

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_reddit(client_id, client_secret, user_agent):
    reddit_session = Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent
    )
    
    with open('reddit_output/used_ids.txt', 'r') as used_reddit_ids: used_reddit_ids = used_reddit_ids.readlines() 
    return reddit_session, used_reddit_ids

def get_posts(reddit_session: Reddit, SUBREDDIT: str, used_reddit_ids: list[str], max_post: int=50):
    now = time()
    posts = [
        post for post in reddit_session.subreddit(SUBREDDIT).top(time_filter="day", limit=max_post) \
        if post.id not in used_reddit_ids
    ]
    posts_ids = [post.id for post in posts]
    with open('reddit_output/used_ids.txt', 'a') as used_reddit_ids:
        used_reddit_ids.write('\n'.join(posts_ids))
        used_reddit_ids.write('\n')

    return posts

def markdown_to_text(comment_body):
    # md -> html -> text since BeautifulSoup can extract text cleanly
    html = markdown(comment_body)
    # remove code snippets
    html = re_sub(r'<pre>(.*?)</pre>', ' ', html)
    html = re_sub(r'<code>(.*?)</code >', ' ', html)
    html = re_sub(r'~~(.*?)~~', ' ', html)
    # extract text
    soup = BeautifulSoup(html, "html.parser")
    text = ''.join(soup.findAll(text=True))
    return text

def create_voice_over(ELEVENLABS_API_KEY, comment, comment_id, file_name):
    return AudioFileClip(voice_over(ELEVENLABS_API_KEY, f'reddit_output/VoiceOvers/{file_name}-{comment_id}.wav', comment))
    
def get_content_from_post(ELEVENLABS_API_KEY: str, post):
    cleans_comments = [(markdown_to_text(comment.body), comment.id) for comment in post.comments[:50]]
    file_name = f'{post.title.replace(" ", "_")}-{post.id}'
    title_voice_over = create_voice_over(
        ELEVENLABS_API_KEY, post.title, 'title', file_name
    )
    comments_voice_over = [(
        comment, 
        comment_id, 
        create_voice_over(
            ELEVENLABS_API_KEY, comment, comment_id, file_name
        )
        ) for comment, comment_id in cleans_comments]
    
    return file_name, post.title, title_voice_over, comments_voice_over, [comment.id for comment in post.comments], post.url

def _setup_driver(post_url: str) -> (webdriver.Firefox, WebDriverWait):
    options = webdriver.FirefoxOptions()
    options.headless = False
    options.enable_mobile = False
    driver = webdriver.Firefox(options=options)
    wait = WebDriverWait(driver, 10)
    driver.set_window_size(width=400, height=800)
    driver.get(post_url)
    return driver, wait

def _take_screenshot(file_name, comment_id, driver, wait, handle='Post'):
    try:
        method = By.CLASS_NAME if (handle == "Post") else By.ID
        search = wait.until(EC.presence_of_element_located((method, handle)))
        driver.execute_script("window.focus();")
        with open(f'reddit_output/Screenshots/{file_name}-{comment_id}.png', 'wb') as screenshot:
            screenshot.write(search.screenshot_as_png)
        return f'reddit_output/Screenshots/{file_name}-{comment_id}.png'
    except:
        return None

def take_post_screenshots(file_name, comments_ids, post_url):
    driver, wait = _setup_driver(post_url)
    element = driver.find_element_by_tag_name("embed-snippet-share-button")

    # Récupération du handle (attribut postid)
    handle = element.get_attribute("postid")
    title_screenshot = _take_screenshot(file_name, 'title', driver, wait, f'post-title-{handle}')
    comments_screenshot = list(filter(None.__ne__, [_take_screenshot(file_name, comment_id, driver, wait, f"t1_{comment_id}-comment-rtjson-content") for comment_id in comments_ids]))
    driver.quit()
    return title_screenshot, comments_screenshot

def create_clip(screenshot, voiceover, margin_size, width):
    imageClip = ImageClip(
        screenshot,
        duration=voiceover.duration
        ).set_position(("center", "center"))
    imageClip = imageClip.resize(width=(width-margin_size))
    videoClip = imageClip.set_audio(voiceover)
    videoClip.fps = 1
    return videoClip

def main(margin_size=64):
    load_dotenv()
    ELEVENLABS_API_KEY = str(getenv('ELEVENLABS_API_KEY'))
    REDDIT_CLIENT_ID = str(getenv('REDDIT_CLIENT_ID'))
    REDDIT_CLIENT_SECRET = str(getenv('REDDIT_CLIENT_SECRET'))
    REDDIT_USER_AGENT = str(getenv('REDDIT_USER_AGENT'))
    SUBREDDIT = str(getenv('SUBREDDIT'))

    reddit_session, used_reddit_ids = setup_reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )
    posts = get_posts(reddit_session, SUBREDDIT, used_reddit_ids)
    for post in posts:
        # print(post.__dict__); exit()
        post.comments.replace_more(limit=0)
        ( # Récupération de toutes les informations nécessaire pour crée le clip
            file_name, post_title, title_voice_over,
            comments_voice_over, comments_ids, post_url
        ) = get_content_from_post(ELEVENLABS_API_KEY, post)

        # Capture d'écran des différents posts pour le clip
        title_screenshot, comments_screenshot = take_post_screenshots(file_name, comments_ids, post_url)
        
        # Découpage en nombre de vidéo en fonction du nombre de voice over
        total_duration = 0
        comments_per_videos = []
        tmp_videos = []
        for comments in comments_voice_over:
            comment, comment_id, voice_over = comments
            if total_duration + voice_over.duration <= 58 and total_duration < 58:
                total_duration += voice_over.duration
                tmp_videos.append(comments)
            else:
                comments_per_videos.append((tmp_videos, total_duration))
                total_duration = 0
                tmp_videos = []
        if tmp_videos:
            comments_per_videos.append((tmp_videos, total_duration))

        videos_background = listdir('reddit_output/BackgroundVideos/')
        for index, comments_list, duration in enumerate(comments_per_videos):
            clips = []
            for _index, comments in enumerate(comments_list):
                _, comment_id, comment_voice_over = comments 

                # Récupération du de la video backgroud
                selected_backgroud = videos_background[randint(0, len(videos_background) - 1)]
                video_background = VideoFileClip(
                    filename=f'reddit_output/BackgroundVideos/{selected_backgroud}',
                    audio=False
                )
                width, _ = video_background.size

                # Calculer le nombre de répétitions nécessaires
                nombre_de_repetitions = duration // video_background.duration

                # Répéter le clip le nombre de fois calculé
                clip_repete = concatenate_videoclips([video_background]*int(nombre_de_repetitions))

                # Si la durée souhaitée n'est pas un multiple exact de la durée du clip,
                # nous devons ajouter le temps restant
                if duration % video_background.duration != 0:
                    temps_restant = duration % video_background.duration
                    clip_restant = video_background.subclip(0, temps_restant)
                    video_background = concatenate_videoclips([clip_repete, clip_restant])

                if _index == 0:
                    title_clip = create_clip(title_screenshot, title_voice_over, margin_size, width)
                    clips.append(title_clip)
                
                comment_screenshot = [f'reddit_output/Screenshots/{screenshot_file}' for screenshot_file in listdir('reddit_output/Screenshots') if comment_id in screenshot_file]
                clips.append(create_clip(comment_screenshot, comment_voice_over, margin_size, width))

            # Merge clips into single track
            content_overlay: VideoFileClip = concatenate_videoclips(clips).set_position(("center", "center"))

            # Compose background/foreground
            final: VideoFileClip = CompositeVideoClip(
                clips=[video_background, content_overlay], 
                size=video_background.size
            ).set_audio(content_overlay.audio)
            final.duration = duration
            final.set_fps(video_background.fps)
            # Write output to file
            print(f"Rendering video {index} for {post_title}...")

            outputFile = f"reddit_output/Videos_to_upload/{post_title}-{index}.mp4"
            final.write_videofile(
                outputFile, 
                codec='mpeg4',
                threads='16', 
                bitrate='8000k'
            )

if __name__ == '__main__': main()

    

    