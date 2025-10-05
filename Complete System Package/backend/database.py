from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


from .config import DATABASE_URL
from .models import Base

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Database dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()