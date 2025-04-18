from fastapi import Depends, Request
from fastapi.responses import StreamingResponse
from app.utils.aichat import kimi_chat_stream
from app.utils.redis import get_redis_client
from app.utils.auth import get_current_user
import json
from fastapi import APIRouter
from app.schemas.aichat import NoteInput


router = APIRouter()
redis_client = get_redis_client()

@router.post("/note", response_model=dict)
async def generate_notes(
    input: NoteInput,
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    redis_key = f"aichat:{user_id}"

    # 1. 读取历史对话
    history = redis_client.get(redis_key)
    if history:
        messages = json.loads(history)
    else:
        # 首轮对话可加 system prompt
        messages = [{"role": "system", "content": "你是一个智能笔记助手。"}]

    # 2. 追加用户输入
    messages.append({"role": "user", "content": input.input})

    async def ai_stream():
        full_reply = ""
        async for content in kimi_chat_stream(messages):
            full_reply += content
            yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
        messages.append({"role": "assistant", "content": full_reply})
        redis_client.set(redis_key, json.dumps(messages), ex=3600)

    return StreamingResponse(ai_stream(), media_type="text/event-stream")

@router.get("/clear", response_model=dict)
async def clear_notes(
    current_user: dict = Depends(get_current_user)
):
    user_id = current_user["id"]
    redis_key = f"aichat:{user_id}"
    redis_client.delete(redis_key)
    return {"msg": "clear successfully"}