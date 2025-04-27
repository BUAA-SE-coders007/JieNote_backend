from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, cast, Date
from datetime import datetime, timedelta
from app.models.model import Note
from app.schemas.note import NoteCreate, NoteUpdate, NoteFind, NoteResponse

async def create_note_in_db(note: NoteCreate, db: AsyncSession):
    new_note = Note(content=note.content, article_id=note.article_id, title=note.title)
    db.add(new_note)
    await db.commit()
    await db.refresh(new_note)
    return new_note

async def delete_note_in_db(note_id: int, db: AsyncSession):
    stmt = select(Note).where(Note.id == note_id)
    result = await db.execute(stmt)
    note = result.scalar_one_or_none()
    if note:
        note.visible = False  # 将 visible 设置为 False，表示删除
        # await db.execute(note)
        await db.commit()
    return note

async def update_note_in_db(note_id: int, note: NoteUpdate, db: AsyncSession):
    stmt = select(Note).where(Note.id == note_id)
    result = await db.execute(stmt)
    existing_note = result.scalar_one_or_none()
    if existing_note:
        if note.title is not None:
            existing_note.title = note.title
        if note.content is not None:
            existing_note.content = note.content
        await db.commit()
        await db.refresh(existing_note)
    return existing_note

async def find_notes_in_db(note_find: NoteFind, db: AsyncSession):
    stmt = select(Note).where(Note.visible == True)  # 只查询可见的笔记

    if note_find.id is not None:
        stmt = stmt.where(Note.id == note_find.id)
    elif note_find.article_id is not None:
        stmt = stmt.where(Note.article_id == note_find.article_id)

    total_count_stmt = select(func.count()).select_from(stmt)
    total_count_result = await db.execute(total_count_stmt)
    total_count = total_count_result.scalar()

    if note_find.page is not None and note_find.page_size is not None:
        offset = (note_find.page - 1) * note_find.page_size
        stmt = stmt.offset(offset).limit(note_find.page_size)

    result = await db.execute(stmt)
    notes = [NoteResponse.model_validate(note) for note in result.scalars().all()]
    return notes, total_count

async def find_notes_title_in_db(note_find: NoteFind, db: AsyncSession):
    stmt = select(Note.title).where(Note.visible == True)  # 只查询可见的笔记

    if note_find.id is not None:
        stmt = stmt.where(Note.id == note_find.id)
    elif note_find.article_id is not None:
        stmt = stmt.where(Note.article_id == note_find.article_id)

    total_count_stmt = select(func.count()).select_from(stmt.subquery())
    total_count_result = await db.execute(total_count_stmt)
    total_count = total_count_result.scalar()

    if note_find.page is not None and note_find.page_size is not None:
        offset = (note_find.page - 1) * note_find.page_size
        stmt = stmt.offset(offset).limit(note_find.page_size)

    result = await db.execute(stmt)
    notes = [row[0] for row in result.fetchall()]
    return notes, total_count

async def find_recent_notes_in_db(db: AsyncSession):
    """
    返回近7天内创建的笔记的数目和对应日期
    """
    # 获取当前日期和7天前的日期
    today = datetime.now().date()
    seven_days_ago = today - timedelta(days=6)

    # 查询近7天内的笔记数目，按日期分组
    stmt = (
        select(
            cast(Note.create_time, Date).label("date"),  # 按日期分组
            func.count(Note.id).label("count")          # 统计每日期的笔记数
        )
        .where(
            Note.create_time >= seven_days_ago,         # 筛选近7天的笔记
            Note.create_time <= today                  # 包括今天
        )
        .group_by(cast(Note.create_time, Date))         # 按日期分组
        .order_by(cast(Note.create_time, Date))         # 按日期排序
    )

    # 执行查询
    result = await db.execute(stmt)
    data = result.fetchall()

    # 格式化结果为字典列表
    recent_notes = [{"date": row.date, "count": row.count} for row in data]

    return recent_notes