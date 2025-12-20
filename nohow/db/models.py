from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Book(Base):
    __tablename__ = 'books'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    chapters = relationship("Chapter", back_populates="book")

class Chapter(Base):
    __tablename__ = 'chapters'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    book_id = Column(Integer, ForeignKey('books.id'))
    book = relationship("Book", back_populates="chapters")
    conversations = relationship("Conversation", back_populates="chapter")

class Conversation(Base):
    __tablename__ = 'conversations'

    id = Column(Integer, primary_key=True)
    content = Column(String, nullable=False)
    chapter_id = Column(Integer, ForeignKey('chapters.id'))
    chapter = relationship("Chapter", back_populates="conversations")
