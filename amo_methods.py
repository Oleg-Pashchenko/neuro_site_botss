import json
import time

import bs4
import requests

import db


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
        headers['access_token'], headers['refresh_token'] = access_token, refresh_token
        payload = {'request[chats][session][action]': 'create'}
        headers['Host'] = host_2
        response = session.post(f'{host}ajax/v1/chats/session', headers=headers, data=payload)
        token = response.json()['response']['chats']['session']['access_token']
    except Exception as e:

        time.sleep(3)
        return get_token(host, mail, password)

    return token, session, headers


def get_pipeline(image, s_name, text, time_string, host, mail, password):
    token, session, _ = get_token(host, mail, password)
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
    _, session, _ = get_token(host, mail, password)
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

            if response.status_code != 200:
                raise Exception("Токен не подошел!")
        except Exception as e:

            token, session, _ = get_token(host, mail, password)
            continue
        break




def create_field(host: str, mail: str, password: str, name: str):
    token, session, headers = get_token(host, mail, password)

    url = f'{host}ajax/settings/custom_fields/'
    data = {
        'action': 'apply_changes',
        'cf[add][0][element_type]': 2,
        'cf[add][0][sortable]': True,
        'cf[add][0][groupable]': True,
        'cf[add][0][predefined]': False,
        'cf[add][0][type_id]': 1,
        'cf[add][0][name]': name,
        'cf[add][0][disabled]': '',
        'cf[add][0][settings][formula]': '',
        'cf[add][0][pipeline_id]': 0
    }
    session.post(url, headers=headers, data=data)


def get_field_by_name(name: str, host: str, mail: str, password: str, lead_id: int) -> (bool, int):
    url = f'{host}leads/detail/{lead_id}'
    token, session, headers = get_token(host, mail, password)
    response = session.get(url)
    if f'"NAME":"{name}"' not in response.text:
        return False, 0
    return True, int(response.text.split(f',"NAME":"{name}"')[0].split('"ID":')[-1])


def get_field_value_by_name(name: str, host: str, mail: str, password: str, lead_id: int) -> (bool, int):
    url = f'{host}leads/detail/{lead_id}'
    token, session, headers = get_token(host, mail, password)
    response = session.get(url)
    if f'"NAME":"{name}"' not in response.text:
        return False, 0

    param_id = int(response.text.split(f',"NAME":"{name}"')[0].split('"ID":')[-1])
    soup = bs4.BeautifulSoup(response.text, features='html.parser')
    status = False
    try:
        value = soup.find('input', {'name': f'CFV[{param_id}]'})['value']
        print(f'{value=}')
        if value == '':
            status = True
    except Exception as e:
        print(e)
    return status, 0


def set_field_by_name(param_id: int, host: str, mail: str, password: str, value: str, lead_id: int, pipeline_id: int):
    url = f'{host}ajax/leads/detail/'
    data = {
        f'CFV[{param_id}]': value,
        'lead[STATUS]': '',
        'lead[PIPELINE_ID]': pipeline_id,
        'ID': lead_id
    }
    token, session, headers = get_token(host, mail, password)
    response = session.post(url, headers=headers, data=data)
    print(response.text)


def fill_field(name, value, host, mail, password, lead_id, pipeline_id):
    exists, param_id = get_field_by_name(name, host, mail, password, lead_id)
    if not exists:
        create_field(host, mail, password, name)
        _, param_id = get_field_by_name(name, host, mail, password, lead_id)
    set_field_by_name(param_id, host, mail, password, value, lead_id, pipeline_id)


def get_field_info(q_m: db.QualificationMode, host, mail, password, lead_id):
    all_fields_qualified, first_uncompleted_field_description, second_uncompleted_field_description, first_field_name = True, '', '', ''
    for k in q_m.q_rules.keys():
        exists, field_id = get_field_value_by_name(k, host, mail, password, lead_id)
        if not exists:
            all_fields_qualified = False
            if first_uncompleted_field_description == '':
                first_field_name = k
                first_uncompleted_field_description = q_m.q_rules[k]
            else:
                second_uncompleted_field_description = q_m.q_rules[k]
                break

    return all_fields_qualified, first_uncompleted_field_description, second_uncompleted_field_description, first_field_name