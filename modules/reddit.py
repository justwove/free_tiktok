from os import getenv
from dotenv import load_dotenv
from praw import Reddit
from time import sleep, time
from markdown import markdown
from re import sub as re_sub
from bs4 import BeautifulSoup
from modules.elevenlabs_api import voice_over
from moviepy.editor import AudioFileClip

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
    return AudioFileClip(voice_over(ELEVENLABS_API_KEY, f'VoiceOvers/{file_name}-{comment_id}.wav', comment))
    
def get_content_from_post(ELEVENLABS_API_KEY: str, post: Reddit.subreddit):
    cleans_comments = [(markdown_to_text(comment.body), comment.id) for comment in post.comments]
    file_name = f'{post.title.replace(" ", "_")}-{post.id}'
    comments_with_voice_over= [(
        create_voice_over(
            ELEVENLABS_API_KEY, post.title, 'title', file_name
        ), 
        comment, 
        comment_id, 
        create_voice_over(
            ELEVENLABS_API_KEY, comment, comment_id, file_name
        )
        ) for comment, comment_id in cleans_comments]
    
    return post.url, cleans_comments, file_name

def main():
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
    


if __name__ == '__main__': main()

    

    