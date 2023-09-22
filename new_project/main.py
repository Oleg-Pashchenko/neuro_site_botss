from typing import Any

from fastapi import FastAPI, Request, Body, Form
from pydantic import BaseModel

app = FastAPI()

from pydantic import BaseModel
from typing import List, Optional


class AccountInfo(BaseModel):
    subdomain: str
    id: str
    _links: dict


class MessageInfo(BaseModel):
    id: str
    chat_id: str
    talk_id: int
    contact_id: int
    text: str
    created_at: int
    element_type: int
    entity_type: str
    element_id: int
    entity_id: int
    type: str
    author: dict


class RequestBody(BaseModel):
    account: AccountInfo
    message: List[MessageInfo]


@app.post("/{username}")
async def main(request_body: RequestBody = Form(...)):
    print(request_body)
    return {"message": "Hello, World!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
