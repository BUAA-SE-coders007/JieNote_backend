from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, cast, Date, insert
from datetime import datetime, timedelta
from app.models.model import Note, self_recycle_bin, Article, Folder
from app.schemas.note import NoteCreate, NoteUpdate, NoteFind, NoteResponse

async def create_note_in_db(note: NoteCreate, db: AsyncSession, user_id: int):
    new_note = Note(content=note.content, article_id=note.article_id, title=note.title, creator_id=user_id)
    db.add(new_note)
    await db.commit()
    await db.refresh(new_note)
    return new_note

async def delete_note_in_db(note_id: int, user_id: int, db: AsyncSession):
    stmt = select(Note).where(Note.id == note_id)
    result = await db.execute(stmt)
    note = result.scalar_one_or_none()
    if note:
        # 将 visible 设置为 False，表示删除
        note.visible = False
        # 找 folder_id
        stmt = select(Article).where(Article.id == note.article_id)
        result = await db.execute(stmt)
        article = result.scalar_one_or_none()
        # 插入 self_recycle_bin 表
        recycle = insert(self_recycle_bin).values(user_id=user_id, type=3, id=note_id, name=note.title, article_id=note.article_id, folder_id=article.folder_id)
        await db.execute(recycle)
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

async def find_notes_in_db(note_find: NoteFind, db: AsyncSession, user_id: int):
    
    stmt = select(Note).where(Note.visible == True)  # 只查询可见的笔记

    if note_find.id is not None:
        stmt = stmt.where(Note.id == note_find.id)
    elif note_find.article_id is not None:
        stmt = stmt.where(Note.article_id == note_find.article_id)
    if note_find.query is not None:
        stmt = stmt.where((Note.content.like(f"%{note_find.query}%") | Note.title.like(f"%{note_find.query}%")) & Note.creator_id == user_id)
    total_count_stmt = select(func.count()).select_from(stmt)
    total_count_result = await db.execute(total_count_stmt)
    total_count = total_count_result.scalar()

    if note_find.page is not None and note_find.page_size is not None:
        offset = (note_find.page - 1) * note_find.page_size
        stmt = stmt.offset(offset).limit(note_find.page_size)

    result = await db.execute(stmt)
    notes = [{"id": note.id, "title": note.title, "content": note.content, "article_id": note.article_id, "is_group": True if note.group_id else False, "create_time": note.create_time, "update_time": note.update_time} for note in result.scalars().all()]
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
    tomorrow = datetime.now().date() + timedelta(days=1)
    seven_days_ago = datetime.now().date() - timedelta(days=6)

    # 查询近7天内的笔记数目，按日期分组
    stmt = (
        select(
            cast(Note.create_time, Date).label("date"),  # 按日期分组
            func.count(Note.id).label("count")          # 统计每日期的笔记数
        )
        .where(
            Note.create_time >= seven_days_ago,         # 筛选近7天的笔记
            Note.create_time < tomorrow                 # 包括今天
        )
        .group_by(cast(Note.create_time, Date))         # 按日期分组
        .order_by(cast(Note.create_time, Date))         # 按日期排序
    )

    # 执行查询
    result = await db.execute(stmt)
    data = result.fetchall()

    # 格式化结果为字典列表
    recent_notes = [{"date": row.date, "count": row.count} for row in data]

    # 若某日期没有记录，则为0
    for i in range(0, 7):
        if i == len(recent_notes) or recent_notes[i].get("date") != seven_days_ago + timedelta(days=i):
            recent_notes.insert(i, {"date": seven_days_ago + timedelta(days=i), "count": 0})

    return recent_notes

async def  find_self_recent_notes_in_db(db: AsyncSession, user_id: int):
    """
    返回近7天内创建的笔记的数目和对应日期
    """
    # 获取当前日期和7天前的日期
    tomorrow = datetime.now().date() + timedelta(days=1)
    seven_days_ago = datetime.now().date() - timedelta(days=6)

    # 查询近7天内的笔记数目，按日期分组
    stmt = (
        select(
            cast(Note.create_time, Date).label("date"),  # 按日期分组
            func.count(Note.id).label("count")          # 统计每日期的笔记数
        )
        .join(Article, Note.article_id == Article.id)
        .join(Folder, Article.folder_id == Folder.id)
        .where(
            Note.visible == True,
            Article.visible == True,
            Folder.visible == True,
            Note.create_time >= seven_days_ago,         # 筛选近7天的笔记
            Note.create_time < tomorrow,                # 包括今天
            Note.creator_id == user_id                  # 筛选特定用户的笔记
        )
        .group_by(cast(Note.create_time, Date))         # 按日期分组
        .order_by(cast(Note.create_time, Date))         # 按日期排序
    )

    # 执行查询
    result = await db.execute(stmt)
    data = result.fetchall()

    # 格式化结果为字典列表
    recent_notes = [{"date": row.date, "count": row.count} for row in data]

    # 若某日期没有记录，则为0
    for i in range(0, 7):
        if i == len(recent_notes) or recent_notes[i].get("date") != seven_days_ago + timedelta(days=i):
            recent_notes.insert(i, {"date": seven_days_ago + timedelta(days=i), "count": 0})

    return recent_notes

async def find_self_notes_count_in_db(db: AsyncSession, user_id: int):
    """
    返回用户的笔记数目
    """
    stmt = (
        select(func.count(Note.id))
        .join(Article, Note.article_id == Article.id)
        .join(Folder, Article.folder_id == Folder.id)
        .where(
            Note.creator_id == user_id,
            Note.visible == True,
            Article.visible == True,
            Folder.visible == True
        )
    )
    result = await db.execute(stmt)
    count = result.scalar_one_or_none()
    return count

async def get_note_by_id(db: AsyncSession, article_id: int):
    """
    根据 ID 获取笔记
    """
    stmt = select(Note).where(Note.article_id == article_id  and Note.visible == True)
    result = await db.execute(stmt)
    # 返回所有笔记
    notes = result.scalars().all()
    return notes if notes else None