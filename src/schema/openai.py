import os
from enum import StrEnum

import dotenv
from pydantic import BaseModel

dotenv.load_dotenv()


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
    api_key: str
    model: Model = Model.gpt_3_5_turbo
    messages: list[Message]
    stream: bool
