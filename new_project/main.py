import asyncio
import random
import time

import openai
import tornado.ioloop
import tornado.web
from urllib.parse import unquote

import amo
import misc
from models import *

NEW_CLIENT_KEY = 'unsorted[add][0][pipeline_id]'
UPDATE_PIPELINE_KEY = 'leads[update][0][pipeline_id]'


class PostDataHandler(tornado.web.RequestHandler):
    async def _get_request_dict(self):
        decoded_data = unquote(self.request.body.decode('utf-8')).split('&')
        request_dict = {}
        for el in decoded_data:
            params = el.split('=')
            k, v = params[0], params[1]
            request_dict[k] = v
        return request_dict

    async def _update_pipeline_information(self, r_d):
        try:
            if NEW_CLIENT_KEY in r_d.keys():
                lead_id, pipeline_id, status_id = r_d[f'unsorted[add][0][lead_id]'], r_d[
                    f'unsorted[add][0][pipeline_id]'], 0
            else:
                lead_id, pipeline_id, status_id = r_d[f'leads[update][0][id]'], r_d[f'leads[update][0][pipeline_id]'], \
                    r_d['leads[update][0][status_id]']
            result = session.query(Leads).filter_by(id=lead_id).first()

            if result:
                result.pipeline_id, result.status_id = pipeline_id, status_id
            else:
                new_lead = Leads(id=lead_id, pipeline_id=pipeline_id, status_id=status_id)
                session.add(new_lead)
            session.commit()
        except:
            pass

    async def clear_history(self, pipeline_id):
        result = session.query(Leads).filter_by(pipeline_id=pipeline_id).first()
        session.query(Messages).filter(Messages.lead_id == result.id).delete()
        session.commit()

    async def message_already_exists(self, message_id):
        result = session.query(Messages).filter_by(id=message_id).first()
        return True if result else False

    async def _get_messages(self, lead_id, request_settings: RequestSettings):
        message_objects = session.query(Messages).filter_by(lead_id=lead_id).all()[::-1]
        messages = []
        symbols = 16385 if '16k' in request_settings.model else 4097
        symbols = (symbols - request_settings.tokens) * 0.75 - len(request_settings.text)
        for message_obj in message_objects:
            if symbols - len(message_obj.message) <= 0:
                break
            if message_obj.is_bot:
                messages.append({'role': 'assistant', 'content': message_obj.message})
            else:
                messages.append({'role': 'user', 'content': message_obj.message})
            symbols = symbols - len(message_obj.message)
        messages = messages[::-1]
        messages.append({"role": "system", "content": request_settings.text})
        return messages

    async def _get_openai_response(self, request_settings: RequestSettings, lead_id):
        model = request_settings.ft_model if request_settings.ft_model != '' else request_settings.model
        openai.api_key = request_settings.openai_api_key
        response = await openai.ChatCompletion.acreate(
            model=model,
            messages=await self._get_messages(lead_id, request_settings),
            max_tokens=request_settings.tokens,
            temperature=request_settings.temperature
        )
        return response['choices'][0]['message']['content']

    async def _message_is_not_last(self, lead_id, message):
        return not session.query(Messages).filter_by(lead_id=lead_id, is_bot=False).all()[-1].message == message

    async def post(self, username):
        r_d = await self._get_request_dict()
        if NEW_CLIENT_KEY in r_d.keys() or UPDATE_PIPELINE_KEY in r_d.keys():
            await self._update_pipeline_information(r_d)
            return 'ok'
        message_id = r_d['message[add][0][id]']
        if await self.message_already_exists(message_id) or int(r_d['message[add][0][created_at]']) + 30 < int(
                time.time()):
            return 'ok'

        message, lead_id = r_d['message[add][0][text]'].replace('+', ' '), r_d['message[add][0][element_id]']
        user_id_hash = r_d['message[add][0][chat_id]']

        lead = session.query(Leads).filter_by(id=lead_id).first()
        request_settings = RequestSettings(lead.pipeline_id, username)
        if int(lead.status_id) in request_settings.block_statuses:
            print("На данном статусе сделки бот не работает!")
            return 'ok'

        if 'message[add][0][attachment][link]' in r_d.keys():
            if request_settings.voice:
                print('Распознаю гс')
                message = await misc.wisper_detect(r_d['message[add][0][attachment][link]'])
            else:
                print('Отправлено голосовое, но распознование выключено!')
                return 'ok'

        new_message_obj = Messages(id=message_id, message=message, lead_id=lead_id, is_bot=False)
        session.add(new_message_obj)
        session.commit()

        if message == '/restart':
            print('Очищаю историю')
            await self.clear_history(lead.pipeline_id)
            return 'ok'

        response_text = await self._get_openai_response(request_settings, lead_id)

        if await self._message_is_not_last(lead_id, message):
            print('Сообщение не последнее!')
            return 'ok'

        new_message_obj = Messages(id=f'assistant-{random.randint(1000000, 10000000)}', message=response_text,
                                   lead_id=lead_id, is_bot=True)
        session.add(new_message_obj)
        session.commit()

        amo.send_message(user_id_hash, response_text, request_settings.amo_key, request_settings.host,
                         request_settings.user, request_settings.password)
        print('Сообщение отправлено!')


def make_app():
    return tornado.web.Application([
        (r"/(\d+)", PostDataHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(8000, address="0.0.0.0")
    print("Server is running on http://0.0.0.0:8000")
    tornado.ioloop.IOLoop.current().start()
