import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load local .env variables
load_dotenv()

# Try SQLALCHEMY_DATABASE_URL (local), fallback to DATABASE_URL (Railway)
SQLALCHEMY_DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL") or os.getenv("DATABASE_URL")

# Raise error if no database URL found
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("Database URL not set. Check .env or Railway settings.")

# Create the engine for SQLAlchemy
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base for models
Base = declarative_base()

# Dependency for injecting DB session in routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
