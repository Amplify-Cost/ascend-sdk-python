import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import logging

# Load local .env if present (optional for local dev)
load_dotenv()

logger = logging.getLogger(__name__)

# Get DATABASE_URL from environment or use local default
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if not SQLALCHEMY_DATABASE_URL:
    # Default to local PostgreSQL for development
    SQLALCHEMY_DATABASE_URL = "postgresql://localhost:5432/owai_dev"
    logger.warning("DATABASE_URL not set, using local PostgreSQL default")

# Create SQLAlchemy engine with appropriate settings
try:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_pre_ping=True,
        pool_size=20,  # Increased from 5 to handle concurrent requests
        max_overflow=30,  # Increased from 10 for peak loads
        pool_recycle=3600,  # Recycle connections every hour
        # Additional options for better local development
        connect_args={"connect_timeout": 10} if "localhost" in SQLALCHEMY_DATABASE_URL else {}
    )
    logger.info(f"Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    # Create a minimal engine for development
    engine = create_engine(
        "sqlite:///./owai_dev.db",
        pool_pre_ping=True
    )
    logger.warning("Fallback to SQLite database for development")

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
