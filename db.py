import json


def clear_history(id: str):
    content = json.load(open('db.json', mode='r', encoding='UTF-8'))
    content.pop(id)
    with open('db.json', mode='w', encoding='UTF-8') as f:
        f.write(json.dumps(content))
    f.close()


def add_message(id: str, message: str, role: str):
    content = json.load(open('db.json', mode='r', encoding='UTF-8'))
    if id not in content.keys():
        content[id] = []
    content[id].append({'role': role, 'content': message})
    with open('db.json', mode='w', encoding='UTF-8') as f:
        f.write(json.dumps(content))
    f.close()


def read_history(id: str):
    return json.load(open('db.json', mode='r', encoding='UTF-8'))[id]

