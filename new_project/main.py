from typing import Any

from fastapi import FastAPI, Request, Body

app = FastAPI()


@app.post("/{username}")
async def main(payload: Any = Body(None)):
    print(payload)
    return {"message": "Hello, World!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
