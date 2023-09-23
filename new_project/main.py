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

    async def message_already_exists(self, r_d):
        result = session.query(Messages).filter_by(id=r_d['message[add][0][id]']).first()
        return True if result else False

    async def _get_openai_response(self, message, request_settings):
        response = openai.ChatCompletion.create(
            model=model_to_use,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )


    async def post(self, username):
        r_d = await self._get_request_dict()
        if NEW_CLIENT_KEY in r_d.keys() or UPDATE_PIPELINE_KEY in r_d.keys():
            await self._update_pipeline_information(r_d)
            return 'ok'

        if await self.message_already_exists(r_d):
            return 'ok'

        message, pipeline_id = r_d['message[add][0][text]'], r_d['message[add][0][element_id]']
        request_settings = RequestSettings(pipeline_id, username)
        if message == '/restart':
            await self.clear_history(pipeline_id)
            return 'ok'
        print(request_settings)
        # response_text = self._get_openai_response(message, request_settings)


def make_app():
    return tornado.web.Application([
        (r"/(\d+)", PostDataHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(8000, address="0.0.0.0")
    print("Server is running on http://0.0.0.0:8000")
    tornado.ioloop.IOLoop.current().start()

"""{'account[subdomain]': 'appgpt', 'account[id]': '31257294', 'account[_links][self]': 'https://appgpt.amocrm.ru', 'message[add][0][id]': 'd3bac6d3-1b5e-40c2-a054-4e0cfe283edb', 'message[add][0][chat_id]': '54caee02-e383-46d8-a9b7-1fb43f07cffe', 'message[add][0][talk_id]': '100', 'message[add][0][contact_id]': '93589657', 'message[add][0][text]': 'f', 'message[add][0][created_at]': '1695486610', 'message[add][0][element_type]': '2', 'message[add][0][entity_type]': 'lead', 'message[add][0][element_id]': '28455849', 'message[add][0][entity_id]': '28455849', 'message[add][0][type]': 'incoming', 'message[add][0][author][id]': '1db2f5cc-aea4-4f96-8d4f-a256ead5b7b0', 'message[add][0][author][type]': 'external', 'message[add][0][author][name]': 'Oleg', 'message[add][0][author][avatar_url]': 'https://amojo.amocrm.ru/attachments/profiles/1db2f5cc-aea4-4f96-8d4f-a256ead5b7b0/RKCPe-file-1_128x128.jpg', 'message[add][0][origin]': 'telegram'}"""
