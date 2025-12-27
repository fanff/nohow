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


def update_convo_content(app, convo_id: int, new_content: str) -> None:
    from nohow.db.utils import get_session

    engine =app.get_db()
    with get_session(engine) as session:
        convo = session.query(Convo).filter_by(id=convo_id).one()
        convo.content = new_content
        session.commit()



def create_conversation(app, book_id: int, toc_address: str) -> Convo:
    from nohow.db.utils import get_session
    with get_session(app.get_db()) as session:
        new_convo = Convo(
            content="",
            toc_address=toc_address,
            book_id=book_id,
        )
        session.add(new_convo)
        session.commit()
        session.refresh(new_convo)
    return new_convo