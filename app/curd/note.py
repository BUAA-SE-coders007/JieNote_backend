from sqlalchemy.orm import Session
from app.models.model import Note
from app.schemas.note import NoteCreate, NoteUpdate

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