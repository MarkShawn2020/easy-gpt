import json
import os
from typing import Generator, Any

import openai
from fastapi import HTTPException

from openai.openai_object import OpenAIObject
from sse_starlette import EventSourceResponse

from src.config.prompts import NURSE_PROMPT
from src.schema.openai import ChatCompletionBody, Role, Message, Model


def streaming_response(response: Generator[list | OpenAIObject | dict, Any, None]):
    for chunk in response:
        # print("data: ", chunk)
        yield json.dumps(chunk)


def call_pure_gpt(body: ChatCompletionBody):
    # openai.api_base = 'http://49.51.186.136:83/v1/'
    print("messages: ", body.messages)

    # todo: replace using Bearer
    openai.api_key = os.environ.get('OPENAI_API_KEY')

    try:
        response = openai.ChatCompletion.create(**body.model_dump())

        # use `sse` to stream, or normal return
        if body.stream:
            response = EventSourceResponse(streaming_response(response))
            response.ping_interval = 600  # avoid `ping`
        # print(response)
        return response

    except Exception as e:
        raise HTTPException(400, str(e))


def call_medical_gpt(body: ChatCompletionBody):
    body.messages.insert(
        0,
        Message.model_validate({"role": "system", "content": NURSE_PROMPT})
    )
    body.model = Model.gpt_4
    response = call_pure_gpt(body)
    return response
