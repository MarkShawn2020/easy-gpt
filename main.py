from typing import Annotated

import uvicorn
from fastapi import FastAPI, Security, Header

from src.config import ApiBase
from src.models import handle_model
from src.lib.openai import call_pure_gpt
from src.lib.serect import api_key_header
from src.schema.openai import ChatCompletionBody

app = FastAPI(
    version='v1',
    title='EasyGPT - An OpenAI Wrapper',
    description='EasyGPT is an OpenAI wrapper for restful/sdk usage, which is powered by FastAPI, SSE, Pydantic, authored by MarkShawn2020, since Oct 14th, 2023.'
)


@app.post(
    "/v1/chat/completions",
)
async def create_chat_completion(
        body: ChatCompletionBody,
        api_base: Annotated[ApiBase, Header()] = None,
        bearer_header=Security(api_key_header),
):
    # Bearer 只是用于 header，7位之后就是其 sk，如果存在的话，需要传入 openai sdk
    api_key = bearer_header[7:] if bearer_header else bearer_header

    api_base = api_base.value if api_base else None

    body = handle_model(body)
    
    return call_pure_gpt(body=body, api_base=api_base, api_key=api_key)


if __name__ == '__main__':
    uvicorn.run("main:app", host='localhost', port=31014, reload=True)
