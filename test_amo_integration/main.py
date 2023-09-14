from flask import Flask, request

app = Flask(__name__)


@app.route('/', methods=['GET', 'POST'])
def main():
    print(request.form.to_dict())
    return 'ok'


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=5000)
