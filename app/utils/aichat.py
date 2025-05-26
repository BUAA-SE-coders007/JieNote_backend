from openai import AsyncOpenAI
from app.core.config import settings

client = AsyncOpenAI(
    api_key=settings.KIMI_API_KEY,
    base_url="http://47.93.172.156:3001/v1",
)

async def kimi_chat_stream(messages, model="moonshot-v1-32k", temperature=0.3):
    """
    异步AI流式对话工具方法，传入消息列表，流式返回AI回复内容。
    :param messages: List[dict]
    :yield: str，AI回复内容片段
    """
    stream = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        stream=True
    )
    async for chunk in stream:
        content = getattr(chunk.choices[0].delta, "content", None)
        if content:
            yield content


async def kimi_chat(messages, model="moonshot-v1-32k", temperature=0):
    """
    异步但不流式AI对话工具方法，传入消息列表，返回AI回复内容。
    """
    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature
    )
    return response.choices[0].message.content if response.choices else ""