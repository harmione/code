'''
Description: 
Author: zhangweilong
Date: 2025-02-20 08:52:19
LastEditTime: 2025-02-20 09:41:57
LastEditors: zhangweilong
'''
# import getpass
import os

# os.environ["OPENAI_API_KEY"] = getpass.getpass()
os.environ["OPENAI_API_KEY"] = "anything"

from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="llama3.2:3b",base_url="http://localhost:11434/v1")

from langchain_core.messages import HumanMessage

# 单轮对话
resp = model.invoke([HumanMessage(content="Hi! I'm Bob")])
print(resp)

from langchain_core.messages import AIMessage

# 多轮对话，引入历史对话
resp = model.invoke(
    [
        HumanMessage(content="Hi! I'm Bob"),
        AIMessage(content="Hello Bob! How can I assist you today?"),
        HumanMessage(content="What's my name?"),
    ]
)

print(resp)

# 消息历史
# 我们可以使用消息历史类来包装我们的模型，使其具有状态。 这将跟踪模型的输入和输出，并将其存储在某个数据存储中。 未来的交互将加载这些消息，并将其作为输入的一部分传递给链
from langchain_core.chat_history import (
    BaseChatMessageHistory,
    InMemoryChatMessageHistory,
)
from langchain_core.runnables.history import RunnableWithMessageHistory

store = {}


def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


with_message_history = RunnableWithMessageHistory(model, get_session_history)

config = {"configurable": {"session_id": "abc2"}}

response = with_message_history.invoke(
    [HumanMessage(content="Hi! I'm Bob")],
    config=config,
)

response.content