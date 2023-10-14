import json
import os
from enum import StrEnum

import dotenv
import openai
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sse_starlette import EventSourceResponse

dotenv.load_dotenv()

app = FastAPI(version='/v1')


@app.get("/")
async def root():
    return {"message": "Hello World"}


class Model(StrEnum):
    gpt_3_5_turbo = 'gpt-3.5-turbo'
    gpt_4 = 'gpt-4'


class Role(StrEnum):
    user = 'user'
    assistant = 'assistant'
    system = 'system'
    function = 'function'


class Message(BaseModel):
    content: str
    role: Role


class ChatCompletionBody(BaseModel):
    api_key: str = os.environ.get('OPENAI_API_KEY')
    model: Model = Model.gpt_3_5_turbo
    messages: list[Message]
    stream: bool


def streaming_response(response):
    for chunk in response:
        print("data: ", chunk)
        yield json.dumps(chunk)


@app.post("/chat/completions")
async def create_chat_completion(body: ChatCompletionBody):
    try:
        response = openai.ChatCompletion.create(**body.model_dump())

        if body.stream:
            response = EventSourceResponse(streaming_response(response))
            response.ping_interval = 600  # avoid `ping`

        return response

    except Exception as e:
        raise HTTPException(400, str(e))


if __name__ == '__main__':
    uvicorn.run("main:app", host='0.0.0.0', port=8000, reload=True)
