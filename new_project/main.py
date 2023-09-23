import asyncio

import openai
import tornado.ioloop
import tornado.web
from urllib.parse import unquote
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
        symbols = symbols * 3 - len(request_settings.text) - request_settings.tokens
        for message_obj in message_objects:
            if symbols - len(message_obj.message) <= 0:
                break
            if message_obj.is_bot:
                messages.append({'role': 'assistant', 'content': message_obj.message})
            else:
                messages.append({'role': 'user', 'content': message_obj.message})
        messages = messages[::-1]
        messages.append({"role": "system", "content": request_settings.text})
        return messages

    async def _get_openai_response(self, request_settings: RequestSettings, lead_id):
        model = request_settings.ft_model if request_settings.ft_model != '' else request_settings.model
        print(request_settings.openai_api_key)
        openai.api_key = request_settings.openai_api_key
        response = openai.ChatCompletion.create(
            model=model,
            messages=await self._get_messages(lead_id, request_settings),
            max_tokens=request_settings.tokens,
            temperature=request_settings.temperature
        )
        return response['choices'][0]['message']['content']

    async def post(self, username):
        r_d = await self._get_request_dict()
        if NEW_CLIENT_KEY in r_d.keys() or UPDATE_PIPELINE_KEY in r_d.keys():
            await self._update_pipeline_information(r_d)
            return 'ok'

        message_id = r_d['message[add][0][id]']
        if await self.message_already_exists(message_id):
            return 'ok'

        message, lead_id = r_d['message[add][0][text]'], r_d['message[add][0][element_id]']

        new_message_obj = Messages(id=message_id, message=message, lead_id=lead_id, is_bot=False)
        session.add(new_message_obj)

        lead = session.query(Leads).filter_by(id=lead_id).first()
        request_settings = RequestSettings(lead.pipeline_id, username)

        if message == '/restart':
            await self.clear_history(lead.pipeline_id)
            return 'ok'
        print(vars(request_settings))
        #response_text = await self._get_openai_response(request_settings, lead_id)
        #print(response_text)


def make_app():
    return tornado.web.Application([
        (r"/(\d+)", PostDataHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(8000, address="0.0.0.0")
    print("Server is running on http://0.0.0.0:8000")
    tornado.ioloop.IOLoop.current().start()
