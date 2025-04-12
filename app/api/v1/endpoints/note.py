from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.schemas.note import NoteCreate, NoteUpdate
from app.utils.get_db import get_db
from app.curd.note import create_note_in_db, delete_note_in_db, update_note_in_db

router = APIRouter()

@router.post("", response_model=dict)
def create_note(note: NoteCreate, db: Session = Depends(get_db)):
    new_note = create_note_in_db(note, db)
    return {"msg": "Note created successfully", "note_id": new_note.id}

@router.delete("/{note_id}", response_model=dict)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    note = delete_note_in_db(note_id, db)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"msg": "Note deleted successfully"}

@router.put("/{note_id}", response_model=dict)
def update_note(note_id: int, content: str, db: Session = Depends(get_db)):
    note = NoteUpdate(id=note_id, content=content)
    updated_note = update_note_in_db(note_id, note, db)
    if not updated_note:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"msg": "Note updated successfully", "note_id": updated_note.id}