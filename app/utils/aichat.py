from openai import AsyncOpenAI
from app.core.config import settings

client = AsyncOpenAI(
    api_key=settings.KIMI_API_KEY,
    base_url="https://api.moonshot.cn/v1",
)

async def kimi_chat_stream(messages, model="moonshot-v1-8k", temperature=0.3):
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