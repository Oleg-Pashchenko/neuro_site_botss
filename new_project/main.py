import asyncio

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
            lead_id, pipeline_id, status_id = r_d[f'leads[add][0][lead_id]'], r_d[f'leads[add][0][pipeline_id]'], 0
        else:
            lead_id, pipeline_id, status_id = r_d[f'leads[update][0][id]'], r_d[f'leads[update][0][pipeline_id]'], 0
        result = session.query(Leads).filter_by(id=lead_id).first()

        if result:
            result.pipeline_id, result.status_id = pipeline_id, status_id
        else:
            new_lead = Leads(id=lead_id, pipeline_id=pipeline_id, status_id=status_id)
            session.add(new_lead)
        session.commit()

    async def post(self, username):
        r_d = await self._get_request_dict()
        if NEW_CLIENT_KEY in r_d.keys() or UPDATE_PIPELINE_KEY in r_d.keys():
            await self._update_pipeline_information(r_d)
        else:
            print(username)
        return 'ok'


def make_app():
    return tornado.web.Application([
        (r"/(\d+)", PostDataHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(8000, address="0.0.0.0")
    print("Server is running on http://0.0.0.0:8000")
    tornado.ioloop.IOLoop.current().start()

"""
{'account[subdomain]': 'appgpt', 'account[id]': '31257294', 'account[_links][self]': 'https://appgpt.amocrm.ru', 'leads[update][0][id]': '27754599', 'leads[update][0][name]': '', 'leads[update][0][status_id]': '59936194', 'leads[update][0][responsible_user_id]': '0', 'leads[update][0][last_modified]': '1694590926', 'leads[update][0][modified_user_id]': '0', 'leads[update][0][created_user_id]': '0', 'leads[update][0][date_create]': '1694590926', 'leads[update][0][pipeline_id]': '7173574', 'leads[update][0][account_id]': '31257294', 'leads[update][0][created_at]': '1694590926', 'leads[update][0][updated_at]': '1694590926'}
{'account[subdomain]': 'appgpt', 'account[id]': '31257294', 'account[_links][self]': 'https://appgpt.amocrm.ru', 'message[add][0][id]': 'a0ce13c7-4825-4ecc-9dc0-b35c49b86db4', 'message[add][0][chat_id]': '54caee02-e383-46d8-a9b7-1fb43f07cffe', 'message[add][0][talk_id]': '100', 'message[add][0][contact_id]': '93589657', 'message[add][0][text]': 'f', 'message[add][0][created_at]': '1695482791', 'message[add][0][element_type]': '2', 'message[add][0][entity_type]': 'lead', 'message[add][0][element_id]': '27754599', 'message[add][0][entity_id]': '27754599', 'message[add][0][type]': 'incoming', 'message[add][0][author][id]': '1db2f5cc-aea4-4f96-8d4f-a256ead5b7b0', 'message[add][0][author][type]': 'external', 'message[add][0][author][name]': 'Oleg', 'message[add][0][author][avatar_url]': 'https://amojo.amocrm.ru/attachments/profiles/1db2f5cc-aea4-4f96-8d4f-a256ead5b7b0/RKCPe-file-1_128x128.jpg', 'message[add][0][origin]': 'telegram'}

{'account[subdomain]': 'appgpt', 'account[id]': '31257294', 'account[_links][self]': 'https://appgpt.amocrm.ru', 'leads[update][0][id]': '27754599', 'leads[update][0][name]': '', 'leads[update][0][status_id]': '59936202', 'leads[update][0][old_status_id]': '59936198', 'leads[update][0][responsible_user_id]': '10004026', 'leads[update][0][last_modified]': '1695482894', 'leads[update][0][modified_user_id]': '10004026', 'leads[update][0][created_user_id]': '0', 'leads[update][0][date_create]': '1694590926', 'leads[update][0][pipeline_id]': '7173574', 'leads[update][0][account_id]': '31257294', 'leads[update][0][created_at]': '1694590926', 'leads[update][0][updated_at]': '1695482894'}
{'account[subdomain]': 'appgpt', 'account[id]': '31257294', 'account[_links][self]': 'https://appgpt.amocrm.ru', 'leads[update][0][id]': '27754599', 'leads[update][0][name]': '', 'leads[update][0][status_id]': '59936206', 'leads[update][0][old_status_id]': '59936202', 'leads[update][0][responsible_user_id]': '10004026', 'leads[update][0][last_modified]': '1695482907', 'leads[update][0][modified_user_id]': '10004026', 'leads[update][0][created_user_id]': '0', 'leads[update][0][date_create]': '1694590926', 'leads[update][0][pipeline_id]': '7173574', 'leads[update][0][account_id]': '31257294', 'leads[update][0][created_at]': '1694590926', 'leads[update][0][updated_at]': '1695482907'}


{'account[subdomain]': 'appgpt', 'account[id]': '31257294', 'account[_links][self]': 'https://appgpt.amocrm.ru', 'unsorted[add][0][uid]': '00b625866db8641999f48766d61d4d0663c12aa38b9bcb4d2866b0c49605', 'unsorted[add][0][source]': 'telegram:29e8f8c6-7557-5f5f-8642-2789ef3f3a13', 'unsorted[add][0][source_uid]': 'amojo:telegram:54caee02-e383-46d8-a9b7-1fb43f07cffe', 'unsorted[add][0][category]': 'chats', 'unsorted[add][0][source_data][from]': 'Oleg', 'unsorted[add][0][source_data][name]': 'Oleg', 'unsorted[add][0][source_data][to]': '29e8f8c6-7557-5f5f-8642-2789ef3f3a13', 'unsorted[add][0][source_data][date]': '1695484695', 'unsorted[add][0][source_data][service]': 'telegram', 'unsorted[add][0][source_data][site]': 'Telegram', 'unsorted[add][0][source_data][client][name]': 'Oleg', 'unsorted[add][0][source_data][client][id]': '1398715343', 'unsorted[add][0][source_data][client][picture]': 'https://amojo.amocrm.ru/attachments/profiles/1db2f5cc-aea4-4f96-8d4f-a256ead5b7b0/RKCPe-file-1_128x128.jpg', 'unsorted[add][0][source_data][origin][provider]': 'amojo', 'unsorted[add][0][source_data][origin][chat_id]': '54caee02-e383-46d8-a9b7-1fb43f07cffe', 'unsorted[add][0][source_data][data][0][id]': '3175b0e9-852b-47f5-b501-61e6e681e014', 'unsorted[add][0][source_data][data][0][manager]': '0', 'unsorted[add][0][source_data][data][0][date]': '1695484695', 'unsorted[add][0][source_data][data][0][text]': 'v', 'unsorted[add][0][source_data][source_uid]': 'amojo:telegram:54caee02-e383-46d8-a9b7-1fb43f07cffe', 'unsorted[add][0][source_data][source]': 'telegram:29e8f8c6-7557-5f5f-8642-2789ef3f3a13', 'unsorted[add][0][source_data][source_name]': 'AICHATTESTBOT', 'unsorted[add][0][date_create]': '1695484695', 'unsorted[add][0][data][contacts][0][id]': '93589657', 'unsorted[add][0][pipeline_id]': '7173574', 'unsorted[add][0][account_id]': '31257294', 'unsorted[add][0][source_id]': '22594646', 'unsorted[add][0][lead_id]': '28455371', 'unsorted[add][0][created_at]': '1695484695'}
"""
