import json
import time
import openai
import os
import dotenv
import requests
from flask import Flask, request
import misc
import db
import amo
import psycopg2

dotenv.load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

app = Flask(__name__)


def get_chat_history(receiver_id, host, mail, password, chat_id):
    while True:
        try:
            headers = {'X-Auth-Token': token}
            url = f'https://amojo.amocrm.ru/messages/{chat_id}/merge?stand=v15' \
                  f'&offset=0&limit=100&chat_id%5B%5D={receiver_id}&get_tags=true&lang=ru'
            chat_history = requests.get(url, headers=headers).json()['message_list']

        except Exception as e:
            print(e, 1)
            token, session, headers = amo.get_token(host, mail, password)
            continue
        break
    return chat_history


def add_salebot_context(chat_history, user_id):
    db.add_message(user_id, chat_history[1], 'assistant')
    db.add_message(user_id, chat_history[0], 'user')

def sync_db(chat_h, stop_phrase, user_id):
    for i in chat_h[1::]:
        if i['text'] != stop_phrase:
            db.add_message(user_id, i['text'], 'assistant')
        else:
            break

def get_db_info(username):
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST'),
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD')
    )
    cur = conn.cursor()
    cur.execute("SELECT * FROM request_settings WHERE owner_name=%s;", (username,))
    info = cur.fetchone()
    conn.close()
    api_key = info[0]
    user, password, host, amo_key = info[3], info[4], info[2], info[5]
    return api_key, user, password, host, amo_key


@app.route('/<username>', methods=["POST"])
def main(username):
    api_key, user, password, host, amo_key = get_db_info(username)
    request_dict = request.form.to_dict()
    print(request_dict)
    if 'unsorted[add][0][pipeline_id]' in request_dict.keys():
        db1 = json.load(open('users_db.json', 'r', encoding='UTF-8'))
        db1[request_dict['unsorted[add][0][lead_id]']] = request_dict['unsorted[add][0][pipeline_id]']
        with open('users_db.json', 'w', encoding='UTF-8') as f:
            f.write(json.dumps(db1))
        f.close()
        print('Новый клиент')
        return 'ok'
    elif 'leads[update][0][pipeline_id]' in request_dict.keys():
        if int(request_dict['leads[update][0][updated_at]']) + 5 < int(time.time()): return 'ok'
        print('Обновление Pipeline')
        print(request_dict)
        fl = False
        db1 = json.load(open('users_db.json', 'r', encoding='UTF-8'))
        try:
            if request_dict['leads[update][0][pipeline_id]'] != db1[request_dict['leads[update][0][id]']]:
                fl = True
        except:
            fl = True
        db1[request_dict['leads[update][0][id]']] = request_dict['leads[update][0][pipeline_id]']
        with open('users_db.json', 'w', encoding='UTF-8') as f:
            f.write(json.dumps(db1))
        f.close()
        if fl:
            db1 = json.load(open('db.json', 'r', encoding='UTF-8'))
            db1[request_dict['leads[update][0][id]']] = []
            with open('db.json', 'w', encoding='UTF-8') as f:
                f.write(json.dumps(db1))
            f.close()
        return 'ok'
    else:
        print('Обычное сообщение')
    text = request_dict['message[add][0][text]']
    print('Q:', text)

    user_id = request_dict['message[add][0][entity_id]']
    user_id_hash = request_dict['message[add][0][chat_id]']
    chat_history = get_chat_history(user_id_hash, host, user, password, amo_key)
    db_history = db.read_history(user_id)

    if len(db_history) == 0 and len(chat_history) == 2:
        add_salebot_context(chat_history, user_id)

    if db_history[-1]['content'] != chat_history[1]['text']:
        sync_db(chat_history, db_history[-1]['content'], user_id)

    if int(request_dict['message[add][0][created_at]']) + 30 < int(time.time()): return 'ok'
    print('success')

    #time.sleep(340)


    bred = json.load(open('users_db.json', 'r', encoding='UTF-8'))

    pipeline, pipeline_name = request_dict['message[add][0][entity_id]'], bred[
        request_dict['message[add][0][entity_id]']]
    p_id = pipeline_name
    misc.add_new_message_stats(p_id)
    misc.get_chats_count_by_pipeline(pipeline_id=p_id, host=host, mail=user, password=password)

    print('Pipeline:', pipeline, 'ChatId:', user_id, 'Pipeline_name', pipeline_name)
    if pipeline is None: return 'ok'
    params = misc.get_params(pipeline_name)

    if 'message[add][0][attachment][link]' in request_dict.keys():
        print('Voice message detected!')
        if params[6] == 1:
            text = misc.wisper_detect(request_dict['message[add][0][attachment][link]'])
        else:
            return 'ok'
    if text == '/restart':
        db.clear_history(user_id)
        return 'ok'
    messages = [{"role": "system", "content": misc.get_annotation(pipeline_name)}]

    db.add_message(user_id, text, 'user')

    translation = misc.translate_to_russian(text)
    #amo.send_notes(pipeline, translation, host, user, password)
    print('Q_T:', translation)
    messages += db.read_history(user_id)
    print('Message history length:', len(messages))
    model_to_use = params[2]
    if params[3] != '':
        model_to_use = params[3]
    response = openai.ChatCompletion.create(
        model=model_to_use,
        messages=messages,
        max_tokens=params[4],
        temperature=params[5]
    )
    tokens_usage = response['usage']['total_tokens']
    misc.add_new_cost_stats(pipeline_id=p_id, additional_cost=tokens_usage)
    response = response['choices'][0]['message']['content']
    response = response.replace('[ссылка]', '').replace('[link]', '')
    db.add_message(user_id, response, 'assistant')
    print()
    amo.send_message(user_id_hash, response, amo_key, host, user, password)
    print('A:', response)
    translation = misc.translate_to_russian(response)
    #amo.send_notes(pipeline, translation, host, user, password)
    print('A_T:', translation)
    return 'ok'


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8000)
