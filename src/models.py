from src.lib.parser import load_prompt
from src.schema.openai import ChatCompletionBody, Model


def handle_model(body: ChatCompletionBody) -> ChatCompletionBody:
    if body.model == Model.bc_medical_1012_control:
        body.add_system_prompt(load_prompt("prompts/1012/control.prompt"))
        body.model = Model.gpt_4

    elif body.model == Model.bc_medical_1012_diagnosis:
        body.add_system_prompt(load_prompt("prompts/1012/diagnosis.prompt"))
        body.model = Model.gpt_4

    elif body.model == Model.bc_medical_1012_consult:
        body.add_system_prompt(load_prompt("prompts/1012/consult.prompt"))
        body.model = Model.gpt_4

    elif body.model == Model.bc_medical_1012_knowledge:
        body.add_system_prompt(load_prompt("prompts/1012/knowledge.prompt"))
        body.model = Model.gpt_4
    return body
