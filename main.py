import json
import time
import openai
import os
import dotenv
from flask import Flask, request
import misc
import db
import amo

dotenv.load_dotenv()
openai.api_key = os.getenv('OPENAI_API_KEY')

app = Flask(__name__)


@app.route('/', methods=["POST"])
def main():
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
    if int(request_dict['message[add][0][created_at]']) + 30 < int(time.time()): return 'ok'
    print('success')
    if 'message[add][0][attachment][link]' in request_dict.keys():
        print('Voice message detected!')
        text = misc.wisper_detect(request_dict['message[add][0][attachment][link]'])

    bred = json.load(open('users_db.json', 'r', encoding='UTF-8'))
    pipeline, pipeline_name = request_dict['message[add][0][entity_id]'], bred[
        request_dict['message[add][0][entity_id]']]

    print('Pipeline:', pipeline, 'ChatId:', user_id, 'Pipeline_name', pipeline_name)
    if pipeline is None: return 'ok'

    if text == '/restart':
        db.clear_history(user_id)
        return 'ok'
    print(pipeline_name)
    messages = [{"role": "system", "content": misc.get_annotation(pipeline_name)}]

    db.add_message(user_id, text, 'user')

    translation = misc.translate_to_russian(text)
    amo.send_notes(pipeline, translation)
    print('Q_T:', translation)
    messages += db.read_history(user_id)
    print('Message history length:', len(messages))
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo-16k',
        messages=messages
    )['choices'][0]['message']['content']

    response = response.replace('[ссылка]', '').replace('[link]', '')
    db.add_message(user_id, response, 'assistant')
    amo.send_message(user_id_hash, response)
    print('A:', response)
    translation = misc.translate_to_russian(response)
    amo.send_notes(pipeline, translation)
    print('A_T:', translation)
    return 'ok'


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8000)

