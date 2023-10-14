import asyncio
import json
import logging
import time
from copy import deepcopy
from typing import List

import backoff
import openai
import tiktoken
from fastapi import HTTPException
from sse_starlette import EventSourceResponse
from starlette import status

from src.config.msgs import ERR_MSG_NEED_CHARGE
from src.config.openai import CHATGPT_TOKENS_MAX_SEND, CHATGPT_MESSAGE_TOKEN_INTERVAL
from src.ds.general import ID
from src.ds.openai.chatgpt import ChatgptModelType, ChatgptRoleType, DChatgptMessage, IChatgptConversationCreate, \
    IChatgptConversation
from src.ds.user import IUser
from src.ds.website import IWebMessage
from src.libs.db import db_insert_msg, db_push_bill_record, db_insert, openai_users_coll, conversations_coll, \
    messages_coll, users_coll
from src.libs.log import getLogger
from src.libs.openai import openai

logger = getLogger('libs:chatgpt')


def get_chatgpt_content(res) -> str:
    return res['choices'][0]['message']['content']


def rotate_chatgpt_prompts(prompts: List[DChatgptMessage], model: ChatgptModelType) -> None:
    """
    todo: based on the start

    :param prompts:
    :param model:
    :return:
    """
    while True:
        token_count_q = calc_chatgpt_cost(prompts, model=model)
        if token_count_q > CHATGPT_TOKENS_MAX_SEND:
            prompts.pop(0 if prompts[0]['role'] != ChatgptRoleType.system else 1)  # 确保第一条system不要被弹出
        else:
            break


def calc_chatgpt_cost(messages: List[DChatgptMessage], model: ChatgptModelType):
    """
    Returns the number of tokens used by a list of messages.

    ref: https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
    """
    try:
        encoding = tiktoken.encoding_for_model(model.value)
    except KeyError:
        logger.warning("Warning: model not found. Using cl100k_base encoding.")
        encoding = tiktoken.get_encoding("cl100k_base")

    # note: frontend use this name
    if model == 'gpt-3.5':
        model = "gpt-3.5-turbo-0301"

    if model == "gpt-3.5-turbo":
        logger.debug("Warning: gpt-3.5-turbo may change over time. Returning num tokens assuming gpt-3.5-turbo-0301.")
        return calc_chatgpt_cost(messages, model=ChatgptModelType.gpt_35_0301)
    elif model == "gpt-4":
        logger.debug("Warning: gpt-4 may change over time. Returning num tokens assuming gpt-4-0314.")
        return calc_chatgpt_cost(messages, model=ChatgptModelType.gpt_4_0314)
    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = 4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif model == "gpt-4-0314":
        tokens_per_message = 3
        tokens_per_name = 1
    else:
        raise NotImplementedError(
            f"""num_tokens_from_messages() is not implemented for model {model}.
            See https://github.com/openai/openai-python/blob/main/chatml.md
            for information on how messages are converted to tokens.""")
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(encoding.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens


class ChatGPTConversation:

    def __init__(self, conversation_id: ID, user_id: ID):

        # user level
        self._user_id = user_id
        self._user: IUser = IUser.parse_obj(
            users_coll.find_one({"_id": self._user_id})
        )
        self._cost = 0  # todo: how to calc cost

        # conversation level
        self._id = conversation_id
        conversation = conversations_coll.find_one({"_id": self._id})
        if conversation:
            self._conversation = IChatgptConversation.parse_obj(conversation)
        else:
            self._conversation = create_chatgpt_conversation(self._id, IChatgptConversationCreate(user_id=user_id))
        logger.info(self._conversation)

        self._platform_type = self._conversation.platform_type
        self._model: ChatgptModelType = self._conversation.platform_params.model

        # todo: how to integrate system prompt
        # message level
        self._prompts: List[DChatgptMessage] = [
            {
                "role": ChatgptRoleType.system,
                "content": self._conversation.platform_params.system_prompt
            },
            *messages_coll.find(
                {"conversation_id": conversation_id},
                {"_id": 0, "role": "$platform_params.role", "content": 1},  # role 目前不是顶级字段！
            )]
        logger.info(self._prompts)

    def pre_check_cost(self, msg_q: IWebMessage):
        self._cost = self._estimate_cost(msg_q)
        if self._cost > self._user.openai.balance:
            raise HTTPException(status.HTTP_402_PAYMENT_REQUIRED, ERR_MSG_NEED_CHARGE)
        db_insert_msg(msg_q)

    def post_sync_response(self, msg_a: IWebMessage, cost: int):
        logger.info(f"sync response: {msg_a}")
        db_insert_msg(msg_a)
        db_push_bill_record(self._user_id, self._id, -cost, self._platform_type)
        openai_users_coll.update_one(
            {"_id": self._user_id},
            {"$inc": {"balance": -cost, "consumption": cost, "cnt": 1}},
            upsert=True
        )

    def _estimate_cost(self, msg: IWebMessage) -> int:
        logger.debug(f"todo: estimate more robust: {msg}")
        if self._model in [ChatgptModelType.gpt_35, ChatgptModelType.gpt_35_0301]:
            return 4097
        if self._model in [ChatgptModelType.gpt_4, ChatgptModelType.gpt_4_0314]:
            return 8192
        raise NotImplementedError

    def _pre_ask(self, msg: IWebMessage):
        """
        最标准的做法是先push msg，然后调用标准接口进行计算，但是没有那个必要，直接满减比较方便，性能也更高
        """
        self.pre_check_cost(msg)

        self._prompts.append({"role": ChatgptRoleType.user, "content": msg.content})
        rotate_chatgpt_prompts(self._prompts, self._model)

    def create(self, msg: IWebMessage) -> str:
        self._pre_ask(msg)

        msg = deepcopy(msg)
        res = openai.ChatCompletion.create(model=self._model.value, messages=self._prompts)
        msg.sender = "openai"
        msg.content = res['choices'][0]['message']['content']
        msg.platform_params.role = ChatgptRoleType.assistant

        cost = res['usage']['total_tokens']
        self.post_sync_response(msg, cost)
        return msg.content

    def acreate(self, msg: IWebMessage) -> EventSourceResponse:
        self._pre_ask(msg)

        async def gen_streaming_response(_msg):
            """
            ref: https://github.com/openai/openai-cookbook/blob/main/examples/How_to_stream_completions.ipynb
            :return:
            """
            _msg = deepcopy(_msg)
            _msg.sender = 'openai'
            _msg.platform_params.role = ChatgptRoleType.assistant
            _msg.content = ''
            try:
                for chunk in openai.ChatCompletion.create(model=self._model, messages=self._prompts, stream=True):
                    content = chunk["choices"][0]["delta"].get("content", "")
                    # logger.debug({"content": content})
                    await asyncio.sleep(CHATGPT_MESSAGE_TOKEN_INTERVAL)  # 加一点停顿，这样方便前端慢慢打字，也减轻服务器压力，单位：s
                    _msg.content += content
                    yield content
            except Exception as e:
                logger.warning(e)
                content = e.args.__str__()
                _msg.content += content
                yield content
            self._prompts.append({"role": ChatgptRoleType.assistant, "content": _msg.content})
            cost = calc_chatgpt_cost(self._prompts, self._model)
            self.post_sync_response(_msg, cost)

        event = EventSourceResponse(gen_streaming_response(msg))
        event.ping_interval = 600  # avoid `ping`
        # event.ping_message_factory # if ping interval is not enough!
        return event


def create_chatgpt_conversation(conversation_id: ID, conversation: IChatgptConversationCreate) -> IChatgptConversation:
    item = IChatgptConversation.parse_obj(dict(**conversation.dict(), _id=conversation_id))
    db_insert(conversations_coll, item.dict(by_alias=True))
    return item


@backoff.on_exception(backoff.expo, openai.error.RateLimitError)
def call_chatgpt(msg: IWebMessage, stream: bool = False):
    """
    backoff, ref: https://platform.openai.com/docs/guides/rate-limits/rate-limits

    """
    logger.info({"msg": msg.dict(), "stream": stream})
    conversation = ChatGPTConversation(msg.conversation_id, msg.sender)
    if not stream:
        return conversation.create(msg)
    else:
        return conversation.acreate(msg)


if __name__ == '__main__':
    model_ = ChatgptModelType.gpt_35
    prompts_: List[DChatgptMessage] = [
        {
            "role": ChatgptRoleType.user,
            "content": "test"
        }
    ]

    logging.basicConfig(
        filename=f"base-{time.time_ns()}.log",
        filemode='a',
        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
        datefmt='%H:%M:%S',
        level=logging.INFO,
    )
    logger = logging.getLogger("chatgpt")


    def run(mode):
        if mode == 1:
            res = openai.ChatCompletion.create(model=model_, messages=prompts_, stream=False)
            print("res", res)

        elif mode == 2:
            for stream in openai.ChatCompletion.create(model=model_, messages=prompts_, stream=True):
                logger.info(json.dumps(stream))


    run(mode=2)