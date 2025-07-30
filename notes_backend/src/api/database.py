import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

load_dotenv()

POSTGRES_USER = os.getenv("NOTES_DB_USER")
POSTGRES_PASSWORD = os.getenv("NOTES_DB_PASSWORD")
POSTGRES_DB = os.getenv("NOTES_DB_NAME")
POSTGRES_HOST = os.getenv("NOTES_DB_HOST", "localhost")
POSTGRES_PORT = os.getenv("NOTES_DB_PORT", "5432")

DB_URL = (
    f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@"
    f"{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

engine = create_async_engine(DB_URL, future=True, echo=False, poolclass=NullPool)
AsyncSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

# PUBLIC_INTERFACE
async def get_db():
    """Dependency for getting async DB session."""
    async with AsyncSessionLocal() as session:
        yield session
