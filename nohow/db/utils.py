from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base

def setup_database(db_url='sqlite:///local.db'):
    """Set up the database and create tables."""
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    return engine

def get_session(engine):
    """Get a new session for interacting with the database."""
    Session = sessionmaker(bind=engine)
    return Session()
