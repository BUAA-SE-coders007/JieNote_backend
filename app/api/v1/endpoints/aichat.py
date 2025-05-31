from fastapi import Depends, Request
from fastapi.responses import StreamingResponse
from app.utils.aichat import kimi_chat_stream, kimi_chat
from app.utils.redis import get_redis_client
from app.utils.auth import get_current_user
import json
from fastapi import APIRouter
from app.schemas.aichat import NoteInput
from sqlalchemy.ext.asyncio import AsyncSession
from app.utils.get_db import get_db
from app.utils.readPDF import read_pdf
from fastapi import HTTPException


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

@router.get("/review", response_model=dict)
async def review_notes(
    article_id: int,
):
    path = f"/lhcos-data/{article_id}.pdf"
    text = await read_pdf(path)
    text += "\n\n请根据以上内容生成文章综述。"
    async def ai_stream():
        full_reply = ""
        try:
            async for content in kimi_chat_stream([{"role": "user", "content": text}]):
                full_reply += content
                yield f"data: {json.dumps({'content': content}, ensure_ascii=False)}\n\n"
        except Exception as e:
            error_str = str(e)
            if "exceeded model token limit" in error_str:
                raise HTTPException(
                    status_code=413,
                    detail="输入内容过长，超出了模型的token限制"
                )
            # 其他类型的错误重新抛出
            raise
    return StreamingResponse(ai_stream(), media_type="text/event-stream")
    
@router.get("/graph", response_model=dict)
async def generate_graph(
    article_id: int,
    db : AsyncSession = Depends(get_db),
):
    # 读取数据库获取笔记内容
    from app.curd.note import get_note_by_id
    notes = await get_note_by_id(db, article_id)
    if not notes:
        raise HTTPException(status_code=404, detail="Note not found")
    text = f"以下是关于文章ID {article_id} 的笔记内容：\n\n"
    for note in notes:
        text += f"标题: {note.title}\n" if note.title else ""
        text += note.content if note.content else ""
    text += """
    我需要你对于上面的内容生成思维导图，请仅给我返回mermaid代码，不要有其他内容，请保证每个连通子图竖向排列，下面是生成样例，
graph TD
    A[机器学习项目] --> B[数据收集]
    A --> C[数据预处理]
    A --> D[特征工程]
    A --> E[模型选择]
    A --> F[模型训练]
    A --> G[模型评估]
    A --> H[模型部署]

    subgraph 数据预处理
        C1[处理缺失值] --> C2[处理异常值]
        C2 --> C3[数据标准化]
        C3 --> C4[数据编码]
    end

    subgraph 特征工程
        D1[特征选择] --> D2[特征提取]
        D2 --> D3[特征构造]
        D3 --> D4[特征缩放]
    end

    subgraph 模型选择
        E1[线性回归] --> E2[决策树]
        E2 --> E3[支持向量机]
        E3 --> E4[神经网络]
    end

    subgraph 模型训练
        F1[划分训练集和验证集] --> F2[选择损失函数]
        F2 --> F3[选择优化算法]
        F3 --> F4[训练模型]
    end

    subgraph 模型评估
        G1[计算准确率] --> G2[计算召回率]
        G2 --> G3[计算F1分数]
        G3 --> G4[绘制混淆矩阵]
    end

    subgraph 模型部署
        H1[模型保存] --> H2[选择部署平台]
        H2 --> H3[模型集成]
        H3 --> H4[模型监控]
        H4 --> H5[模型更新]
    end

    B --> 数据预处理
    C --> 特征工程
    D --> 模型选择
    E --> 模型训练
    F --> 模型评估
    G --> 模型部署
    """
    try:
        ans = await kimi_chat([{"role": "user", "content": text}], model="moonshot-v1-32k")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"AI服务异常: {str(e)}"
        )
    return {"mermaid_code": ans.strip().replace("```mermaid", "").replace("```", "").strip()}
    