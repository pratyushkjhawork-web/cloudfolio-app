"""
Database connection setup.

Reads DATABASE_URL from the environment if set (e.g. pointing at RDS
MySQL on AWS); falls back to local SQLite if not set, so the exact
same code runs unchanged locally and after deployment.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./cloudfolio.db")

# SQLite needs this extra arg for multi-threaded FastAPI; MySQL doesn't.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a DB session per request, closes it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
