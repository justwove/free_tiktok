import requests


def voice_over(file_path, text):

    CHUNK_SIZE = 1024
    url = "https://api.elevenlabs.io/v1/text-to-speech/pNInz6obpgDQGcFmaJgB"
    with open('.env', 'r') as env_file: api_key = str(env_file.readlines()[0].split('=')[-1]).strip()

    headers = {
    "Accept": "audio/mpeg",
    "Content-Type": "application/json",
    "xi-api-key": api_key
    }

    data = {
    "text": text,
    "model_id": "eleven_monolingual_v1",
    "voice_settings": {
        "stability": 0.5,
        "similarity_boost": 0.5
    }
    }

    response = requests.post(url, json=data, headers=headers)
    if response.text.startswith('{"'):
        print(response.content)
        new_api_key = input('Limit reached, please provide new api key (Just create a tempmail account): ')
        with open('.env', 'r') as env_file: new_env_file = env_file.read().replace(api_key, new_api_key)
        with open('.env', 'w') as env_file: env_file.write(new_env_file)

        return voice_over(file_path, text)
    with open(file_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            if chunk:
                f.write(chunk)
    return file_path

# with open('api_key.env', 'r') as api_key: api_key = api_key.readlines()[0].strip()
# print(api_key); exit()
# voice_over(api_key, 'test.wav', 'Just a test love you <3')
# with open('.env', 'r') as env_file: api_key = str(env_file.readlines()[0].split('=')[-1]).strip()
# voice_over(api_key, 'test.wav', 'Just a test love you <3')


