from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas.note import NoteCreate, NoteUpdate, NoteFind
from app.utils.get_db import get_db
from app.curd.note import create_note_in_db, delete_note_in_db, update_note_in_db, find_notes_in_db, find_notes_title_in_db, find_self_notes_count_in_db, find_self_recent_notes_in_db
from typing import Optional
from app.utils.auth import get_current_user
router = APIRouter()

@router.post("/create", response_model=dict)
async def create_note(note: NoteCreate, db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    new_note = await create_note_in_db(note, db, user_id)
    return {"msg": "Note created successfully", "note_id": new_note.id}

@router.delete("/{note_id}", response_model=dict)
async def delete_note(note_id: int, db: AsyncSession = Depends(get_db)):
    note = await delete_note_in_db(note_id, db)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"msg": "Note deleted successfully"}

@router.put("/{note_id}", response_model=dict)
async def update_note(note_id: int, content: Optional[str] = None, title: Optional[str] = None,db: AsyncSession = Depends(get_db)):
    if content is None and title is None:
        raise HTTPException(status_code=400, detail="At least one field must be provided for update")
    note = NoteUpdate(id=note_id, content=content, title=title)
    updated_note = await update_note_in_db(note_id, note, db)
    if not updated_note:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"msg": "Note updated successfully", "note_id": updated_note.id}

@router.get("/get", response_model=dict)
async def get_notes(note_find: NoteFind = Depends(), db: AsyncSession = Depends(get_db)):
    notes, total_count = await find_notes_in_db(note_find, db)
    return {
        "pagination": {
            "total_count": total_count,
            "page": note_find.page,
            "page_size": note_find.page_size
        },
        "notes": [note.model_dump() for note in notes]
    }

@router.get("/title", response_model=dict)
async def get_notes_title(note_find: NoteFind = Depends(), db: AsyncSession = Depends(get_db)):
    notes, total_count = await find_notes_title_in_db(note_find, db)
    return {
        "pagination": {
            "total_count": total_count,
            "page": note_find.page,
            "page_size": note_find.page_size
        },
        "notes": notes
    }

@router.get("/count", response_model=dict)
async def get_notes_count(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    count = await find_self_notes_count_in_db(db, user_id)
    return {
        "count": count
    }

@router.get("/count/recent", response_model=dict)
async def get_recent_notes_count(db: AsyncSession = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user_id = current_user["id"]
    notes = await find_self_recent_notes_in_db(db, user_id)
    return {
        "notes": notes
    }
