import tornado.ioloop
import tornado.web
import json
from urllib.parse import unquote

# Словарь для хранения данных пользователя
user_data = {}


class PostDataHandler(tornado.web.RequestHandler):
    async def post(self, username):
        print(username)
        decoded_data = unquote(self.request.body.decode('utf-8')).split('&')
        request_dict = {}
        for el in decoded_data:
            params = el.split('=')
            k, v = params[0], params[1]
            request_dict[k] = v

        try:
            data = json.loads(decoded_data)
            user_data[username] = data
            self.write({"message": f"Data for {username} has been received and stored."})
        except Exception as e:
            print(e)
            self.set_status(400)
            self.write({"error": "Invalid data format."})


def make_app():
    return tornado.web.Application([
        (r"/(\d+)", PostDataHandler),
    ])


if __name__ == "__main__":
    app = make_app()
    app.listen(8000, address="0.0.0.0")
    print("Server is running on http://0.0.0.0:8000")
    tornado.ioloop.IOLoop.current().start()
