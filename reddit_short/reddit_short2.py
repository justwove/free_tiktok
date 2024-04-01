# Création des variables d'environnement
from os import getenv, listdir, remove  
from sys import path
from random import randint, choice

# Import des librairies 
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

"""
Classe pour récupérer du contenu sur Reddit et le transformer en vidéos
"""
class Reddit_short:

    def __init__(self, client_id: str, client_secret: str, user_agent: str, subreddit: str) -> None:
       
        # Initialisation de la session Reddit
        self.reddit_session: Reddit = Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent 
        )
        
        # Récupération des ids déjà utilisés
        with open('reddit_output/used_ids.txt', 'r') as used_reddit_ids:  
            self.used_reddit_ids: list[str] = used_reddit_ids.readlines()  

        # Récupération de la clé API 
        with open('.env', 'r') as env_file: env_file=env_file.readlines() 
        self.keys: dict[str] = {
            'ELEVENLABS_API_KEY': env_file[0].split('=')[1]  
        }
        
        # Choix du subreddit
        self.subreddit = subreddit  
        
        # Initialisation de Selenium
        self.setup_selenium()

    """ 
    Configuration de Selenium avec des options pour masquer l'automatisation
    """
    def setup_selenium(self):
       
        # Options Chrome 
        options = webdriver.ChromeOptions() 
        options.add_argument('--log-level=3') 
        options.add_argument('user-data-dir=/mnt/c/Users/Seb/AppData/Local/Google/Chrome/User\ Data') 
        options.add_argument('start-maximized')
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-extensions-file-access-check")
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])

        # Préférences
        prefs = {'profile.managed_default_content_settings.images': 2, 'profile.managed_default_content_settings.video': 2}
        options.add_experimental_option('prefs', prefs)
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option("prefs", {"javascript.enabled": True})

        # Choix aléatoires pour masquer l'automatisation
        options.add_argument('--window-size=' + f"{randint(1024, 1920)}x{randint(768, 1080)}") 
        options.add_argument('--force-timezone=' + choice(['US/Pacific', 'US/Mountain', 'US/Central', 'US/Eastern', 'Canada/Pacific', 'Canada/Mountain', 'Canada/Central', 'Canada/Eastern']))
        options.binary_location = '/usr/bin/google-chrome-stable'

        # Initialisation du driver
        self.driver = webdriver.Chrome(options=options)

        # Masquage de l'automatisation
        stealth(
            self.driver,
            # Choix aléatoires de languages pour masquer l'automatisation 
            languages=[choice(["en-US", "en", "fr", "es", "de", "ja"])],
            
            # Choix aléatoires de vendor pour masquer l'automatisation 
            vendor=choice(["Google Inc.", "Mozilla Foundation", "Microsoft Corporation", "Apple Inc.", "Samsung Electronics", "IBM Corporation", "Facebook, Inc.", "Amazon.com, Inc.", "Twitter, Inc.", "Intel Corporation", "Oracle Corporation", "Adobe Systems Incorporated", "Netflix, Inc.", "PayPal Holdings, Inc.", "Salesforce.com, Inc.", "Uber Technologies, Inc." ]),
            
            # Choix aléatoire de platform pour masquer l'automatisation
            platform=choice(["Win32", "Linux x86_64", "Macintosh", "Android", "iOS", "Windows NT", "Ubuntu", "Fedora", "Chrome OS", "Raspbian", "FreeBSD", "OpenBSD", "Solaris", "PlayStation", "Xbox"]),

            # Choix aléatoire de webgl_vendor pour masquer l'automatisation  
            webgl_vendor=choice(["Intel Inc.", "NVIDIA Corporation", "AMD", "ARM", "Qualcomm", "Apple Inc.", "Broadcom", "Imagination Technologies", "Vivante Corporation", "Mali Technologies" ]),

            # Choix aléatoire de renderer pour masquer l'automatisation
            renderer=choice(["Intel Iris OpenGL Engine", "NVIDIA GeForce GTX", "AMD Radeon", "ARM Mali", "Qualcomm Adreno", "Apple A12 Bionic", "Broadcom VideoCore", "Imagination PowerVR", "Vivante GC Series", "Mali-G77", "Intel UHD Graphics", "AMD Radeon Pro", "NVIDIA Quadro" ])
        )

    def get_posts(self, max_post: int=50):
        """
        Récupère les posts du subreddit 
        """

        # Récupération des posts récents 
        posts = [
            post for post in self.reddit_session.subreddit(self.subreddit).top(time_filter="day", limit=max_post) \
            if post.id not in self.used_reddit_ids
        ]
        
        # Récupération des ids des posts
        posts_ids = [post.id for post in posts]
        
        # Ecriture des ids dans le fichier 
        with open('reddit_output/used_ids.txt', 'a') as used_reddit_ids:
            used_reddit_ids.write('\n'.join(posts_ids))
            used_reddit_ids.write('\n')
            
        # Mise à jour des ids utilisés
        self.used_reddit_ids = posts_ids
        self.posts = posts

    def create_shorts(self, post_id, index):
        # Récupération des clips courts
        for audio_id_list in self.clips:

            # Initialisation du clip
            clip = []

            # Boucle sur les audios  
            for i, audio, id in enumerate(audio_id_list):

                # Ajout du titre au premier tour
                if i == 0: 
                    clip.append(self.title_clip)
                    continue

                # Récupération de la vidéo de fond
                video_background = VideoFileClip(
                    filename=f"reddit_output/background/shorts/{choice(listdir('reddit_output/background/shorts'))}",
                    audio=False
                )

                # Taille vidéo 
                width, _ = video_background.size

                # Création clip commentaire
                comment_clip = ImageClip(
                    f"reddit_output/Screenshots/{id}.png",
                    duration=audio.duration
                ).set_position(('center', 'center'))

                # Redimensionnement
                comment_clip = comment_clip.resize(width=(width-64))

                # Ajout de l'audio 
                comment_clip = comment_clip.set_audio(audio)
                comment_clip.fps = 1

                # Ajout à la liste
                clip.append(comment_clip)

            # Concaténation des clips  
            content_clips = concatenate_videoclips(clip).set_position(("center", "center"))

            # Création du clip final
            final_clip = CompositeVideoClip(
                clips=[video_background, content_clips], 
                size=video_background.size
            )

            # Ajout de l'audio
            final_clip.set_audio(content_clips.audio)  

            # Définition de la durée  
            final_clip.duration = sum([_clip.duration for _clip in clip])

            # Définition des FPS
            final_clip.set_fps(video_background.fps)

            # Affichage 
            print(f'Rendering video {self.posts_content[post_id]["Title"]}')

            # Écriture vidéo finale
            final_clip.write_videofile(
                f'reddit_output/shorts_upload/{self.posts_content[post_id]["Title"]}_{index}.mp4',
                codec='mpeg4',
                threads='16', 
                bitrate='8000k'  
            )

    """
    Prend des captures d'écran du titre et des commentaires
    """
    def take_screenshot(self):

        # Ouvre la page web  
        self.driver.get(self.post_url)
        
        # Attend le chargement
        sleep(2)
        
        # Capture écran titre
        title = (self.current_voice_over[0][1], self.driver.find_element(By.XPATH, f'//*[@id="t3_{self.current_voice_over[0][1]}"]').screenshot_as_png)
        
        # Capture écran commentaires
        comments = [(comment[1], self.driver.find_element(By.XPATH, f'//*[@id="t1_{comment[1]}-comment-rtjson-content"]').screenshot_as_png) for comment in self.current_voice_over[1]]

        # Enregistrement capture écran titre
        with open(f'reddit_output/Screenshots/{title[0]}.png', 'wb') as screenshot_title:
            screenshot_title.write(title[1])

        # Enregistrement captures écran commentaires 
        for comment in comments:
            with open(f'reddit_output/Screenshots/{comment[0]}.png', 'wb') as screenshot_comment:
                screenshot_comment.write(comment[1])
                
    """            
    Prépare les clips pour les shorts
    """ 
    def prepare_shorts(self):

        # Durée par défaut 
        default_duration = self.current_voice_over[0][0].duration  
        duration = default_duration
        
        # Initialisation clips
        self.clips = []
        clip = [self.current_voice_over[0][0]]
        
        # Boucle sur commentaires
        for comment in self.current_voice_over[1]:
        
            # Vérifie durée max
            if duration + comment[0].duration > 60:  
                self.clips.append(clip)
                clip = []
                duration = default_duration

            # Ajout titre si clip vide  
            if clip == []: 
                clip.append(self.current_voice_over[0])
                
            # Mise à jour durée   
            duration += comment[0].duration
            
            # Ajout commentaire  
            clip.append(comment)


    """
    Récupère le contenu des posts (titre, commentaires, url)
    """
    def get_content_from_posts(self):

        # Dictionnaire contenant les infos des posts
        self.posts_content = {
            post.id: {
                'Title': post.title,
                'Comments': [(comment.body, comment.id) for comment in post.comments[:75] if (type(comment) != MoreComments and len(comment.body) > 150)],
                'URL': post.url
            }
        for post in self.posts}
        
        # Boucle sur les posts
        for index, post_id in enumerate(self.posts_content.keys()):
            
            # Récupération audio titre et commentaires
            title_voice_over = (AudioFileClip(voice_over(  
                f'voice_over/{post_id}.wav', self.posts_content[post_id]['Title'] 
            )), post_id)

            comments_voice_over = [
                (AudioFileClip(voice_over( 
                    f'voice_over/{comment_id}.wav', comment                         
                )), comment_id) for comment, comment_id in self.posts_content[post_id]['Comments']]

            # Suite du traitement
            self.current_voice_over = (title_voice_over, comments_voice_over)
            self.post_url = self.posts_content[post_id]['URL']
            self.take_screenshot()
            self.prepare_shorts()

            # Quick fix to change
            video_background = VideoFileClip(
                filename=f"reddit_output/background/{choice(listdir('reddit_output/background/shorts'))}", 
                audio=False
            )

            # Récupération dimensions
            width, _ = video_background.size

            # Création du clip titre 
            self.title_clip = ImageClip(
                f"reddit_output/Screenshots/{title_voice_over[1]}.png",
                duration=title_voice_over[0].duration
            ).set_position(('center', 'center'))

            # Redimensionnement  
            self.title_clip = self.title_clip.resize(width=(width-64))  

            # Ajout de l'audio
            self.title_clip = self.title_clip.set_audio(title_voice_over[0])  

            # Définition des FPS
            self.title_clip.fps = 1

            # Création des shorts
            self.create_shorts(post_id, index)

            # Création de la vidéo "classique"
            self.create_video(post_id, comments_voice_over)


            # Netoyage des fichiers images & audio utilisés
            self.post_ids = [comment_id for _, comment_id in self.posts_content[post_id]['Comments']]
            self.post_ids.append(post_id)
            [remove(f'voice_over/{_id}.wav') for _id in self.post_ids]
            [remove(f'reddit_output/screenshots/{_id}.png') for _id in self.post_ids]

    def create_video(self, post_id, comments_voice_over):
        video_background = VideoFileClip(
            filename=f"reddit_output/background/{choice(listdir('reddit_output/background/shorts'))}", 
            audio=False
        )

        # Récupération dimensions
        width, _ = video_background.size  

        # Initialisation clip
        clip = []   

        # Ajout clip titre
        clip.append(self.title_clip)   

        # Boucle sur commentaires audio
        for comment in comments_voice_over:
            # Création clip commentaire 
            comment_clip = ImageClip(
                    f"reddit_output/Screenshots/{comment[1]}.png",
                    duration=comment[0].duration
                ).set_position(('center', 'center'))

            # Redimensionnement
            comment_clip = comment_clip.resize(width=(width-64))
                
            # Ajout audio
            comment_clip = comment_clip.set_audio(comment[0])
            comment_clip.fps = 1
                
            # Ajout au clip
            clip.append(comment_clip)

        # Concaténation clips
        content_clips = concatenate_videoclips(clip).set_position(("center", "center"))  

        # Création vidéo finale
        final_clip = CompositeVideoClip(
                clips=[video_background, content_clips],
                size=video_background.size 
            )

        # Écriture vidéo finale
        final_clip.write_videofile(
                f'reddit_output/shorts_upload/{self.posts_content[post_id]["Title"]}.mp4',
                codec='mpeg4',
                threads='16', 
                bitrate='8000k'  
            )


