from flask import Flask, request

app = Flask(__name__)


@app.route('/')
def main():
    print(request.form.to_dict())


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=8000)
