from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from typing import List

from markdown_it import MarkdownIt

from src.api.models import User, Note
from src.api.schemas import (
    UserCreate,
    UserRead,
    NoteCreate,
    NoteUpdate,
    NoteRead,
)
from src.api.database import get_db
from src.api.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    decode_jwt_token,
)

app = FastAPI(
    title="Notes Manager API",
    version="1.0",
    description="API backend for the Notes Manager app with markdown support.",
    openapi_tags=[
        {"name": "auth", "description": "User authentication and registration"},
        {"name": "notes", "description": "CRUD for personal notes"},
    ]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")

md = MarkdownIt()

# Helper: get user from JWT.
# PUBLIC_INTERFACE
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    """Dependency to get the current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_jwt_token(token)
    if payload is None:
        raise credentials_exception
    username: str = payload.get("sub")
    if not username:
        raise credentials_exception
    # Fetch user from DB
    user_result = await db.execute(select(User).where(User.username == username))
    user = user_result.scalars().first()
    if user is None:
        raise credentials_exception
    return user

@app.get("/", tags=["health"])
def health_check():
    """Health check endpoint."""
    return {"message": "Healthy"}

# --- User Registration and Auth ---

# PUBLIC_INTERFACE
@app.post("/api/register", response_model=UserRead, tags=["auth"], summary="Register a new user")
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user (username & email must be unique)."""
    existing_user = await db.execute(
        select(User).where((User.username == user.username) | (User.email == user.email))
    )
    if existing_user.scalars().first():
        raise HTTPException(status_code=400, detail="Username or email already registered")
    new_user = User(
        username=user.username,
        email=user.email,
        password_hash=get_password_hash(user.password),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return UserRead.from_orm(new_user)

# PUBLIC_INTERFACE
@app.post("/api/token", summary="Login and get access token", tags=["auth"])
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    """Login returns JWT access token if credentials are valid."""
    result = await db.execute(select(User).where(User.username == form_data.username))
    user = result.scalars().first()
    if user is None or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# --- Notes CRUD ---

# PUBLIC_INTERFACE
@app.post("/api/notes", response_model=NoteRead, tags=["notes"], summary="Create a new note")
async def create_note(note: NoteCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create a new note for the authenticated user."""
    new_note = Note(
        user_id=current_user.id,
        title=note.title,
        content=note.content
    )
    db.add(new_note)
    await db.commit()
    await db.refresh(new_note)
    return NoteRead.from_orm(new_note)

# PUBLIC_INTERFACE
@app.get("/api/notes", response_model=List[NoteRead], tags=["notes"], summary="List all notes")
async def list_notes(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Return all notes for the authenticated user."""
    results = await db.execute(select(Note).where(Note.user_id == current_user.id).order_by(Note.updated_at.desc()))
    notes = results.scalars().all()
    return [NoteRead.from_orm(note) for note in notes]

# PUBLIC_INTERFACE
@app.get("/api/notes/{note_id}", response_model=NoteRead, tags=["notes"], summary="Get note by ID")
async def get_note(note_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Return a single note by its ID (must belong to current user)."""
    result = await db.execute(select(Note).where((Note.id == note_id) & (Note.user_id == current_user.id)))
    note = result.scalars().first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return NoteRead.from_orm(note)

# PUBLIC_INTERFACE
@app.put("/api/notes/{note_id}", response_model=NoteRead, tags=["notes"], summary="Update a note")
async def update_note(note_id: int, note: NoteUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Update an existing note, only for owner."""
    result = await db.execute(select(Note).where((Note.id == note_id) & (Note.user_id == current_user.id)))
    db_note = result.scalars().first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")
    if note.title is not None:
        db_note.title = note.title
    if note.content is not None:
        db_note.content = note.content
    await db.commit()
    await db.refresh(db_note)
    return NoteRead.from_orm(db_note)

# PUBLIC_INTERFACE
@app.delete("/api/notes/{note_id}", tags=["notes"], status_code=204, summary="Delete a note")
async def delete_note(note_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Delete a note. Must be owner."""
    result = await db.execute(select(Note).where((Note.id == note_id) & (Note.user_id == current_user.id)))
    db_note = result.scalars().first()
    if not db_note:
        raise HTTPException(status_code=404, detail="Note not found")
    await db.delete(db_note)
    await db.commit()
    return

# PUBLIC_INTERFACE
@app.get("/api/notes/{note_id}/render", response_class=HTMLResponse, tags=["notes"], summary="Render Markdown note as HTML")
async def render_note_markdown(note_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Render note content (markdown) as HTML for preview."""
    result = await db.execute(select(Note).where((Note.id == note_id) & (Note.user_id == current_user.id)))
    note = result.scalars().first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    html = md.render(note.content or "")
    return HTMLResponse(content=html, status_code=200)
