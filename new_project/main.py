from typing import Dict, List, AnyStr, Any, Union

from fastapi import FastAPI

app = FastAPI()

JSONObject = Dict[AnyStr, Any]
JSONArray = List[Any]
JSONStructure = Union[JSONArray, JSONObject]


@app.post("/{username}")
async def main(username: str, request: JSONStructure):
    print(username, request)
    return {"message": "Hello, World!"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
