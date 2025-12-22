from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Book(Base):
    __tablename__ = "books"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    toc = Column(Text, nullable=True)
    toc_tree = Column(Text, nullable=True)
    chapter_contents = relationship(
        "Chapter",
        cascade="all, delete-orphan",
    )
    conversations = relationship(
        "Convo",
        cascade="all, delete-orphan",
    )

    def get_toc_extract(self, min_line: int, max_line: int) -> str:
        if self.toc:
            # simple line-based extract
            lines = self.toc.splitlines()
            return "\n".join(lines[min_line:max_line])
        else:
            return ""


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True)
    content = Column(String, nullable=False)
    toc_address = Column(
        String, nullable=False
    )  # something like 1.2.3 to identify location in TOC
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)


class Convo(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True)
    content = Column(String, nullable=False)
    toc_address = Column(
        String, nullable=True
    )  # something like 1.2.3 to identify location in TOC
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)


def update_convo_content(convo_id: int, new_content: str) -> None:
    from nohow.db.utils import get_session
    from nohow.db.utils import setup_database

    engine = setup_database()
    with get_session(engine) as session:
        convo = session.query(Convo).filter_by(id=convo_id).one()
        convo.content = new_content
        session.commit()
