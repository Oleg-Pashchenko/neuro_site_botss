import random
import time

import tornado.ioloop
import tornado.web
from urllib.parse import unquote
import db, openai_methods
from utils.constants import *
from utils import misc
import amo_methods
import gdown

class PostDataHandler(tornado.web.RequestHandler):
    async def _get_request_dict(self):
        decoded_data = unquote(self.request.body.decode('utf-8')).split('&')
        request_dict = {}
        for el in decoded_data:
            params = el.split('=')
            k, v = params[0], params[1]
            request_dict[k] = v
        return request_dict

    async def post(self, username):
        r_d = await self._get_request_dict()
        if NEW_CLIENT_KEY in r_d.keys() or UPDATE_PIPELINE_KEY in r_d.keys():
            await db.update_pipeline_information(r_d)
            return 'Сделка успешно создана!'

        message_id = r_d[MESSAGE_ID_KEY]
        if await db.message_already_exists(message_id) or int(r_d[MESSAGE_CREATION_KEY]) + 30 < int(time.time()):
            return 'Сообщение уже распознавалось!'

        message, lead_id, user_id_hash = r_d[MESSAGE_KEY].replace('+', ' '), r_d[LEAD_KEY], r_d[USER_ID_HASH_KEY]

        lead = await db.get_leads(lead_id)
        request_settings = db.RequestSettings(lead.pipeline_id, username)

        if int(lead.status_id) in request_settings.block_statuses:
            return "На данном статусе сделки бот не работает!"

        if VOICE_MESSAGE_KEY in r_d.keys():
            if request_settings.voice:
                message = await misc.wisper_detect(r_d['message[add][0][attachment][link]'])
            else:
                return 'Отправлено голосовое, но распознование выключено!'

        await db.add_new_message(message_id=message_id, message=message, lead_id=lead_id, is_bot=False)

        if message == RESTART_KEY:
            await db.clear_history(lead.pipeline_id)
            return 'История успешно очищена!'

        response_text = await openai_methods.get_openai_response(request_settings, lead_id, message)

        if await db.message_is_not_last(lead_id, message):
            return 'Сообщение не последнее! Обработка прервана!'

        new_message_id = f'assistant-{random.randint(1000000, 10000000)}'
        await db.add_new_message(message_id=new_message_id, message=response_text, lead_id=lead_id, is_bot=True)

        amo_methods.send_message(user_id_hash, response_text, request_settings.amo_key, request_settings.host,
                                 request_settings.user, request_settings.password)
        return 'Сообщение отправлено!'


class SyncDatabaseHandler(tornado.web.RequestHandler):
    async def post(self, google_drive_url):
        file_id = google_drive_url.split("/")[-2]
        gdown.download(f"https://drive.google.com/uc?id={file_id}", f"files/{file_id}.xlsx", quiet=True)


def make_app():
    return tornado.web.Application([
        (r"/api/v2/(\d+)", PostDataHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(5000, address="0.0.0.0")
    print("Server is running on http://0.0.0.0:8000")
    tornado.ioloop.IOLoop.current().start()
