"""
Database Session Management
Provides database connection and session handling
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from core.config import settings

# Create engine
engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_pre_ping=True
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """
    Dependency for FastAPI routes to get database session
    Automatically handles session lifecycle
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
