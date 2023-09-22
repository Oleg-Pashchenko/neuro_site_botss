from fastapi import FastAPI, Request

app = FastAPI()


@app.get("/{username}")
async def main(username: str, request: Request):
    print(username, request.json())
    return {"message": "Hello, World!"}
