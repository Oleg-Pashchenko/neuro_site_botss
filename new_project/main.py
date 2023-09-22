from fastapi import FastAPI, Request

app = FastAPI()


@app.post("/{username}")
async def main(username: str, request: Request):
    print(username, await request.json())
    return {"message": "Hello, World!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)