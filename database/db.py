import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session

# Load environment variables
load_dotenv()

# Get DB URL from environment or default to local SQLite db
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///database.db")

# Create engine. SQLite needs check_same_thread=False for Streamlit's multi-threaded model
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

# Create session factory
session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
SessionLocal = scoped_session(session_factory)

# Declarative base for models
Base = declarative_base()

def get_db():
    """
    Context manager or helper for DB sessions.
    Guarantees session cleanup after execution.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
