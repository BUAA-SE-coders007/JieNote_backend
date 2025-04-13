from sqlalchemy.orm import Session
from app.models.model import Note
from app.schemas.note import NoteCreate, NoteUpdate, NoteFind, NoteResponse

def create_note_in_db(note: NoteCreate, db: Session):
    new_note = Note(content=note.content, article_id=note.article_id)
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    return new_note

def delete_note_in_db(note_id: int, db: Session):
    note = db.query(Note).filter(Note.id == note_id).first()
    if note:
        db.delete(note)
        db.commit()
    return note

def update_note_in_db(note_id: int, note: NoteUpdate, db: Session):
    existing_note = db.query(Note).filter(Note.id == note_id).first()
    if existing_note:
        existing_note.content = note.content
        db.commit()
        db.refresh(existing_note)
    return existing_note

def find_notes_in_db(note_find: NoteFind, db: Session):
    query = db.query(Note)

    if note_find.id is not None:
        query = query.filter(Note.id == note_find.id)
    elif note_find.article_id is not None:
        query = query.filter(Note.article_id == note_find.article_id)

    totol_count = query.count()
    # 添加分页逻辑
    if note_find.page is not None and note_find.page_size is not None:
        offset = (note_find.page - 1) * note_find.page_size
        query = query.offset(offset).limit(note_find.page_size)
    notes = [NoteResponse.model_validate(note) for note in query.all()]
    return notes, totol_count
