import json
import warnings
import amo_methods
import db
from utils import misc

warnings.simplefilter(action='ignore', category=FutureWarning)

import openai
import pandas as pd

openai.api_key = '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'


def get_question_db_function(filename):
    df = pd.read_excel(filename)
    list_of_arrays = df.to_dict(orient='records')
    if len(list_of_arrays) == 0:
        return None
    first_row = list(df.iloc[:, 0])

    response = [{
        "name": "Function",
        "description": "Get flat request",
        "parameters": {
            "type": "object",
            "properties": {'Question': {'type': 'string', 'enum': first_row}},
            'required': ['Question']
        }
    }]
    return response


def get_check_question_answer_db_function(question):
    return [{
        "name": "Function",
        "description": "Function description",
        "parameters": {
            "type": "object",
            "properties": {'is_correct':
                               {'type': 'boolean',
                                'description': question,
                                }},
            'required': ['is_correct']
        }
    }]


def get_answer_by_question(question, filename):
    answer = None
    try:
        df = pd.read_excel(filename)
        list_of_arrays = list(df.iloc)
        for i in list_of_arrays:
            if i[0] == question:
                answer = i[1]
                break
    except:
        pass
    return answer


def get_keywords_values(message, func):
    messages = [
        {'role': 'system', 'content': 'Give answer:'},
        {"role": "user",
         "content": message}]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=messages,
        functions=func,
        function_call="auto"
    )
    response_message = response["choices"][0]["message"]
    if response_message.get("function_call"):
        function_args = json.loads(response_message["function_call"]["arguments"])
        return {'is_ok': True, 'args': function_args}
    else:
        return {'is_ok': False, 'args': {}}


def perephrase(message):
    response = openai.ChatCompletion.create(
        model='gpt-3.5-turbo',
        messages=[{"role": "system", "content": 'Перефразируй'},
                  {'role': 'user', 'content': message}],
        max_tokens=4000,
        temperature=1
    )
    return response['choices'][0]['message']['content']


def question_mode(user_message, filename, db_error_message, openai_error_message):
    print('Получено сообщение:', user_message)
    func = get_question_db_function(filename)
    response = get_keywords_values(user_message, func)

    if not response['is_ok']:
        return openai_error_message
    answer = get_answer_by_question(response['args']['Question'], filename)
    if answer is None:
        return db_error_message
    print("Квалифицирован вопрос:", response['args']['Question'])
    print('Получен ответ из базы данных:', answer)
    response = perephrase(answer)
    print('Перефразирован ответ:', response)
    return response


def check_question_answer(question, answer):
    func = get_check_question_answer_db_function(question)
    resp = get_keywords_values(f"{answer}", func)
    return resp


def execute(message, request_settings: db.RequestSettings, lead_id, user_id_hash):
    filename = request_settings.qualification_mode.file_link
    q_m = request_settings.qualification_mode
    misc.download_file(filename, request_settings)
    is_first_message = False
    bot_answers_count = db.get_bots_answers_count(lead_id)
    if bot_answers_count == 0:
        is_first_message = True

    if is_first_message:
        resp = perephrase(q_m.hi_message)
        amo_methods.send_message(user_id_hash, resp, request_settings.amo_key, request_settings.host,
                                 request_settings.user, request_settings.password)
        return resp

    all_fields_qualified, first_uncompleted_field_description, \
        second_uncompleted_field_description, first_field_name = amo_methods.get_field_info(q_m, request_settings.host,
                                                                                            request_settings.user,
                                                                                            request_settings.password,
                                                                                            lead_id)

    if not all_fields_qualified:
        answer_correct = check_question_answer(first_uncompleted_field_description, message)

        if answer_correct['is_ok'] is True and answer_correct['args']['is_correct'] is True:
            amo_methods.fill_field(first_field_name, message, request_settings.host, request_settings.user,
                                   request_settings.password, lead_id, request_settings.id)
            if second_uncompleted_field_description == '':
                question = perephrase("Все ок. В будущем здесь будет резюмирующее сообщение!")
            else:
                question = perephrase(second_uncompleted_field_description)
            amo_methods.send_message(user_id_hash, question, request_settings.amo_key, request_settings.host,
                                     request_settings.user, request_settings.password)
            return question

    answer = question_mode(message, filename, q_m.db_error_message, q_m.openai_error_message)

    amo_methods.send_message(user_id_hash, answer, request_settings.amo_key, request_settings.host,
                             request_settings.user, request_settings.password)

    if not all_fields_qualified:
        question = perephrase(first_uncompleted_field_description)
        amo_methods.send_message(user_id_hash, question, request_settings.amo_key, request_settings.host,
                                 request_settings.user, request_settings.password)

        return f'{answer}\n\n{question}'
    return answer
