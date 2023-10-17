import os

import db
from utils.constants import *
import json
import pandas as pd
import openai


async def get_openai_response(request_settings: db.RequestSettings, lead_id, message):
    model = request_settings.ft_model if request_settings.ft_model != '' else request_settings.model
    openai.api_key = request_settings.openai_api_key

    if request_settings.working_mode == DEFAULT_WORKING_MODE:
        response = await openai.ChatCompletion.acreate(
            model=model,
            messages=await db.get_messages(lead_id, request_settings),
            max_tokens=request_settings.tokens,
            temperature=request_settings.temperature
        )
        return response['choices'][0]['message']['content']
    else:
        return execute_db_mode(message, request_settings)


def get_function(filename):
    df = pd.read_excel(filename)
    list_of_arrays = df.to_dict(orient='records')
    if len(list_of_arrays) == 0:
        return None

    result = {}
    for d in list_of_arrays:
        for k, v in d.items():
            if k not in result.keys():
                if str(v).isdigit():
                    result[k] = {"type": "integer"}
                    continue
                result[k] = {"type": "string", 'enum': []}
            if result[k]['type'] == 'string' and v not in result[k]['enum']:
                result[k]['enum'].append(v)
    response = [{
        "name": "Function",
        "description": "Get flat request",
        "parameters": {
            "type": "object",
            "properties": result,
            'required': list(result.keys())
        }
    }]
    return response


def find_from_database(filename, params, rules):
    df = pd.read_excel(filename)
    list_of_arrays = df.to_dict(orient='records')
    responses = []
    to_view = []
    for d in list_of_arrays:
        approved = True
        for k, v in d.items():
            try:
                if rules[k] == '=' and v != params[k]:
                    approved = False
                elif rules[k] == '>=' and not (v >= params[k]):
                    """Введенное значение должно быть больше или равно заданому"""
                    approved = False
                elif rules[k] == '<=' and not (v <= params[k]):
                    approved = False
                elif rules[k] == '>' and not (v > params[k]):
                    approved = False
                elif rules[k] == '<' and not (v < params[k]):
                    approved = False
                elif rules[k] == '!' and not (k in to_view):
                    to_view.append(k)
            except:
                pass
            if not approved:
                break
        if approved:
            responses.append(d)
    return responses, to_view


def prepare_to_answer(choices, to_view):
    resp = ""
    for i, choice in enumerate(choices):
        text = ''
        for v in to_view:
            text += choice[v] + ' '
        try:
            resp += f'\n[{i + 1}] {text}'
        except:
            pass
    return resp


def get_keywords_values(message):
    messages = [
        {'role': 'system', 'content': 'Give answer:'},
        {"role": "user",
         "content": message}]
    func = get_function('Avatarex.xlsx')
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


def execute_db_mode(request_message, request_settings: db.RequestSettings):
    rules = request_settings.work_rule
    db_name = 'files/' + request_settings.filename

    if not os.path.exists(db_name):
        print('Donwloading file')
        import gdown
        file_id = request_settings.file_link.split("/")[-2]
        try:
            download_url = f"https://drive.google.com/uc?id={file_id}"
            output_path = f"files/{file_id}.xlsx"
            gdown.download(download_url, output_path, quiet=True)
        except:
            return 'Please, connect database file!'

    answer_messages = {'openai_error': request_settings.openai_error_message,
                       'db_error': request_settings.db_error_message,
                       'success': request_settings.success_message,
                       'start': request_settings.hi_message}
    openai_response = get_keywords_values(request_message)

    if openai_response['is_ok'] is True:
        choices, to_view = find_from_database(db_name, openai_response['args'], rules)
        if len(choices) == 0:
            return answer_messages['db_error']
        else:
            prepared_message = prepare_to_answer(choices, to_view)
            return answer_messages['success'] + '\n' + prepared_message
    else:
        return answer_messages['openai_error']
