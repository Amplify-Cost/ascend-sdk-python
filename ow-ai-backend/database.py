import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load local .env if present (optional for local dev)
load_dotenv()

# Use DATABASE_URL provided by Railway automatically
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("DATABASE_URL not set. Ensure Railway Postgres is attached and injected.")

# Create SQLAlchemy engine with recommended production settings
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base
Base = declarative_base()

# Dependency for injecting DB session in routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
