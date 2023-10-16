from typing import Annotated

import uvicorn
from fastapi import FastAPI, Header, HTTPException
from regex import regex

from src.config.prompts import NURSE_PROMPT
from src.core import call_pure_gpt
from src.lib.parser import parse_api_key
from src.schema.openai import ChatCompletionBody, Model, Message

app = FastAPI(
    version='v1',
    title='EasyGPT - An OpenAI Wrapper',
    description='EasyGPT is an OpenAI wrapper for restful/sdk usage, which is powered by FastAPI, SSE, Pydantic, authored by MarkShawn2020, since Oct 14th, 2023.'
)


@app.post(
    "/v1/chat/completions",
)
async def create_chat_completion(
        authorization: Annotated[str, Header()],
        body: ChatCompletionBody):
    if body.model == Model.medical_gpt:
        body.messages.insert(
            0,
            Message.model_validate({"role": "system", "content": NURSE_PROMPT})
        )
        body.model = Model.gpt_4

    api_key = parse_api_key(authorization)
    if not api_key:
        raise HTTPException(400, '需要在 Headers 中提供 Authorization: Bearer sk...')
    return call_pure_gpt(api_key, body)


if __name__ == '__main__':
    uvicorn.run("main:app", host='localhost', port=31014, reload=True)
