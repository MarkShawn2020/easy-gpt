import uvicorn
from fastapi import FastAPI

from src.core import call_pure_gpt, call_medical_gpt
from src.schema.openai import ChatCompletionBody, Model

app = FastAPI(
    version='v1',
    title='EasyGPT - An OpenAI Wrapper',
    description='EasyGPT is an OpenAI wrapper for restful/sdk usage, which is powered by FastAPI, SSE, Pydantic, authored by MarkShawn2020, since Oct 14th, 2023.'
)


@app.post(
    "/v1/chat/completions",
)
async def create_chat_completion(body: ChatCompletionBody):
    if body.model == Model.medical_gpt:
        return call_medical_gpt(body)
    return call_pure_gpt(body)


if __name__ == '__main__':
    uvicorn.run("main:app", host='localhost', port=31014, reload=True)
