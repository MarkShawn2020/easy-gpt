import json
from typing import Generator, Any

import dotenv
import openai
import uvicorn
from fastapi import FastAPI, HTTPException
from openai.openai_object import OpenAIObject
from sse_starlette import EventSourceResponse

from src.schema.openai import ChatCompletionBody

app = FastAPI(
    version='/v1',
    title='EasyGPT - An OpenAI Wrapper',
    description='EasyGPT is an OpenAI wrapper for restful/sdk usage, which is powered by FastAPI, SSE, Pydantic, authored by MarkShawn2020, since Oct 14th, 2023.'
)


def streaming_response(response: Generator[list | OpenAIObject | dict, Any, None]):
    for chunk in response:
        print("data: ", chunk)
        yield json.dumps(chunk)


@app.post(
    "/v1/chat/completions",
)
async def create_chat_completion(body: ChatCompletionBody):
    try:
        response = openai.ChatCompletion.create(**body.model_dump())

        # use `sse` to stream, or normal return
        if body.stream:
            response = EventSourceResponse(streaming_response(response))
            response.ping_interval = 600  # avoid `ping`

        return response

    except Exception as e:
        raise HTTPException(400, str(e))


if __name__ == '__main__':
    uvicorn.run("main:app", host='localhost', port=31014, reload=True)
