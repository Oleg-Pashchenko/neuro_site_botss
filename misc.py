import json
import os

import whisper
import openai
import psycopg2
import os
import dotenv

from amo import get_token

dotenv.load_dotenv()


def get_annotation(pipeline) -> str:
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    cur = conn.cursor()
    cur.execute("SELECT text FROM pipelines WHERE pipeline_id=%s", (pipeline,))
    resp = cur.fetchone()
    conn.close()
    return resp[0]


def get_params(pipeline):
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    cur = conn.cursor()
    cur.execute("SELECT * FROM pipelines WHERE pipeline_id=%s", (pipeline,))
    resp = cur.fetchone()
    conn.close()
    return resp


def has_russian_symbols(text, alphabet=set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')):
    return not alphabet.isdisjoint(text.lower())


def translate_to_russian(text):
    if has_russian_symbols(text):
        return text
    messages = [
        {'role': 'assistant', 'content': "Переведи текст на русский язык"},
        {'role': 'user', 'content': text}
    ]
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=messages
    )['choices'][0]['message']['content']
    return response


def wisper_detect(link: str):
    import requests
    r = requests.get(link, allow_redirects=True)
    open('file.m4a', 'wb').write(r.content)
    model = whisper.load_model("base")

    # load audio and pad/trim it to fit 30 seconds
    audio = whisper.load_audio('file.m4a')
    audio = whisper.pad_or_trim(audio)

    # make log-Mel spectrogram and move to the same device as the model
    mel = whisper.log_mel_spectrogram(audio).to(model.device)
    _, probs = model.detect_language(mel)
    print(f"Detected language: {max(probs, key=probs.get)}")
    options = whisper.DecodingOptions(fp16=False)
    result = whisper.decode(model, mel, options)
    return result.text


def get_chats_count_by_pipeline(pipeline_id, host, mail, password):
    url = f'https://chatgpt.amocrm.ru/ajax/leads/sum/{pipeline_id}/'
    token, session = get_token(host, mail, password)
    response = session.post(url)
    print(response.text)



def get_stats_info(pipeline_id):
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    cur = conn.cursor()
    cur.execute("SELECT * FROM stats WHERE pipeline_id=%s", (pipeline_id,))
    resp = cur.fetchone()
    conn.close()
    return resp


def add_new_message_stats(pipeline_id):
    pass


def add_new_cost_stats(pipeline_id, additional_cost):
    pass
