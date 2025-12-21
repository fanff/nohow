from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    toc = Column(Text, nullable=True)

    conversations = relationship("Conversation", back_populates="book")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    content = Column(String, nullable=False)
    chapter_id = Column(Integer, ForeignKey("chapters.id"))
    book = relationship("Book", back_populates="conversations")
