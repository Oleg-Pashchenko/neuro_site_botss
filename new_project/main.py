from fastapi import FastAPI, Body

app = FastAPI()


@app.post("/{username}")
async def main(username: str, message: dict = Body(...)):
    print(username, message)
    return {"message": "Hello, World!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
