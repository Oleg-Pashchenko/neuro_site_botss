import json
import os
import time

import bs4
import requests


def get_token(host, mail, password):
    host_2 = host.replace('https://', '').replace('/', '')
    try:
        session = requests.Session()
        response = session.get(host)
        session_id = response.cookies.get('session_id')
        csrf_token = response.cookies.get('csrf_token')
        headers = {
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Cookie': f'session_id={session_id}; '
                      f'csrf_token={csrf_token};'
                      f'last_login={mail}',
            'Host': host.replace('https://', '').replace('/', ''),
            'Origin': host,
            'Referer': host,
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36'
        }
        payload = {
            'csrf_token': csrf_token,
            'password': password,
            'temporary_auth': "N",
            'username': mail}

        response = session.post(f'{host}oauth2/authorize', headers=headers, data=payload)
        access_token = response.cookies.get('access_token')
        refresh_token = response.cookies.get('refresh_token')
        print(access_token)
        print(refresh_token)
        headers['access_token'], headers['refresh_token'] = access_token, refresh_token
        payload = {'request[chats][session][action]': 'create'}
        headers['Host'] = host_2
        response = session.post(f'{host}ajax/v1/chats/session', headers=headers, data=payload)
        token = response.json()['response']['chats']['session']['access_token']
    except Exception as e:
        print(e)
        time.sleep(3)
        return get_token(host, mail, password)
    print('Amo Token:', token)
    return token, session


def get_pipeline(image, s_name, text, time_string, host, mail, password):
    token, session = get_token(host, mail, password)
    pipelines = json.load(open('config.json'))['pipelines']
    for pipeline in pipelines:
        pip1 = pipeline
        url = f'{host}leads/pipeline/{pipeline}/?skip_filter=Y'

        response = session.get(url, timeout=15)
        soup = bs4.BeautifulSoup(response.text, features='html.parser')
        for i in soup.find_all('div', {'class': 'pipeline-unsorted__item-data'}):
            img = i.find('div', {'class': 'pipeline-unsorted__item-avatar'}). \
                get('style').replace("background-image: url(", '').replace(')', '')
            message_time = i.find('div', {'class': 'pipeline-unsorted__item-date'}).text

            name = i.find('a', {'class': 'pipeline-unsorted__item-title'}).text
            message = i.find('div', {'class': 'pipeline_leads__linked-entities_last-message__text'}).text
            pipeline = i.find('a', {'class': 'pipeline-unsorted__item-title'}).get('href').split('/')[-1]
            if (img == image) or (message == text and s_name == name):
                return pipeline, pip1
    return None  # message[add][0][entity_id] || message[add][0][element_id]


# Для leads[update][0][id] поставлен статус leads[update][0][status_id] в leads[update][0][pipeline_id]


def send_notes(pipeline_id, text, host, mail, password):
    _, session = get_token(host, mail, password)
    url = f'{host}private/notes/edit2.php?parent_element_id={pipeline_id}&parent_element_type=2'
    data = {
        'DATE_CREATE': int(time.time()),
        'ACTION': 'ADD_NOTE',
        'BODY': text,
        'ELEMENT_ID': pipeline_id,
        'ELEMENT_TYPE': '2'
    }
    resp = session.post(url, data=data)


def send_message(receiver_id: str, message: str, account_chat_id, host, mail, password, token=''):
    while True:
        try:
            headers = {'X-Auth-Token': token}
            url = f'https://amojo.amocrm.ru/v1/chats/{account_chat_id}/' \
                  f'{receiver_id}/messages?with_video=true&stand=v15'
            response = requests.post(url, headers=headers, data=json.dumps({"text": message}))
            print(response.status_code)
            if response.status_code != 200:
                raise Exception("Токен не подошел!")
        except Exception as e:
            print(e, 2)
            token, session = get_token(host, mail, password)
            continue
        break
