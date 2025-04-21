from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.models.model import Note
from app.schemas.note import NoteCreate, NoteUpdate, NoteFind, NoteResponse

async def create_note_in_db(note: NoteCreate, db: AsyncSession):
    new_note = Note(content=note.content, article_id=note.article_id)
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
        await db.execute(note)
        await db.commit()
    return note

async def update_note_in_db(note_id: int, note: NoteUpdate, db: AsyncSession):
    stmt = select(Note).where(Note.id == note_id)
    result = await db.execute(stmt)
    existing_note = result.scalar_one_or_none()
    if existing_note:
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
