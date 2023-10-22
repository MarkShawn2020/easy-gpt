import os
from enum import StrEnum

import dotenv
from pydantic import BaseModel

dotenv.load_dotenv()


class Model(StrEnum):
    gpt_3_5_turbo = 'gpt-3.5-turbo'
    gpt_4 = 'gpt-4'
    bc_medical_1012_control = 'bc_medical_1012_control'
    bc_medical_1012_diagnosis = 'bc_medical_1012_diagnosis'
    bc_medical_1012_knowledge = 'bc_medical_1012_knowledge'
    bc_medical_1012_consult = 'bc_medical_1012_consult'


class Role(StrEnum):
    user = 'user'
    assistant = 'assistant'
    system = 'system'
    function = 'function'


class Message(BaseModel):
    content: str = "突然头疼是怎么回事？"
    role: Role = Role.user


class ChatCompletionBody(BaseModel):
    temperature: float = .01
    model: Model = Model.gpt_3_5_turbo
    messages: list[Message]
    stream: bool = False

    def add_system_prompt(self, content: str):
        self.messages.insert(0, Message.model_validate({
            "role": "system",
            "content": content
        }))
