from textual.binding import Binding
from textual import on
from typing import List
import json
from nohow.mkdutils import TocTreeNode
from textual.screen import Screen

from textual.widgets import Footer, Header, TextArea, Static, ContentSwitcher, Button

from nohow.db.models import Book, Convo, Chapter
from nohow.db.utils import get_session, setup_database
from nohow.textual_comp.screens.tocedit import BookEditWidget
from textual.containers import Horizontal

from nohow.textual_comp.widgets.chatflow import (
    ChapterView,
    ChatFlowWidget,
    ChatList,
    ChatListItem,
)


class TOCReaderScreen(Screen):
    """Écran de lecture / conversation sur un chapitre (placeholder)."""

    DEFAULT_CSS = """
    TOCReaderScreen {


    }
    TOCReaderScreen > #main_area {
        height: 1fr;
        width: 100%;
        
    }
    #chat_list {
        width: 1fr;
        
    }
    #chat_area_switcher {

        width: 3fr;
        height: 100%;
        
    }
    """
    BINDINGS = [
        Binding("ctrl+e", "book_list", "Book List"),
    ]

    def __init__(self, book_id: int, **kwargs) -> None:
        super().__init__(**kwargs)
        self.book_id = book_id
        self.book: Book | None = None

    def compose(self):
        yield Header()

        with Horizontal(id="main_area"):
            yield ChatList(id="chat_list")
            yield ContentSwitcher(id="chat_area_switcher")
            # yield ChatFlowWidget(book_id=self.book_id, chapter_id=1, id="chat_area")
        yield Footer()

    @on(ChatList.ChatOpened)
    def on_chat_select(self, event: ChatList.ChatOpened) -> None:
        chat_area_switcher = self.query_one("#chat_area_switcher", ContentSwitcher)
        event.item
        assert isinstance(event.item, ChatListItem)
        if event.item.is_title:
            toc_index = event.item.toc_index
            convo_id = f"convo_{toc_index.replace('.', '_')}"
            chat_area_switcher.current = convo_id
        else:
            convo_id = (
                f"convo_{event.item.toc_index.replace('.', '_')}{event.item.chat_id}"
            )
            chat_area_switcher.current = convo_id

    def on_mount(self) -> None:
        self.run_worker(self._refresh_from_db(), exclusive=True)

    async def _refresh_from_db(self) -> None:

        engine = setup_database()
        with get_session(engine) as session:
            book = session.query(Book).filter_by(id=self.book_id).one()
            all_chapters: List[Chapter] = list(book.chapter_contents)
            all_convo: List[Convo] = list(book.conversations)
            self.book = book
        # loading the chat list
        chat_list = self.query_one("#chat_list", ChatList)
        chat_list.current_book = book
        chat_list.all_convo = all_convo
        chat_list.load_conversation_list_items()

        # loading the content switch with chat areas
        chat_area_switcher = self.query_one("#chat_area_switcher", ContentSwitcher)
        # one chat per TOC Node identified by the toc Address
        toc_tree = TocTreeNode.from_json(json.loads(book.toc_tree))
        for node in toc_tree.preorder():
            # add a chat area for this node
            assert isinstance(node, TocTreeNode)
            convo_key = node.conversation_key()
            # find if there is a chapter content for this node
            chapter_contents = [c for c in all_chapters if c.toc_address == convo_key]

            chat_widget = ChapterView(
                book=book,
                tocnode=node,
                toc_address=convo_key,
                chapter_content=chapter_contents[0].content if chapter_contents else "",
            )
            chat_area_switcher.add_content(chat_widget, id=chat_widget.widget_id)
        for convo in all_convo:
            assert isinstance(convo.toc_address, str)
            # conversation are identified by their toc_address and inner numbering
            chat_widget = ChatFlowWidget(
                book=book,
                toc_address=convo.toc_address,
                convo_id=convo.id,
                convo_content=convo.content or "",
            )
            widget_id = chat_widget.widget_id
            chat_area_switcher.add_content(chat_widget, id=widget_id)

    def _create_conversation(self, toc_address: str) -> Convo:
        engine = setup_database()
        with get_session(engine) as session:
            book = session.query(Book).filter_by(id=self.book_id).one()
            new_convo = Convo(
                content="",
                toc_address=toc_address,
                book_id=self.book_id,
            )
            session.add(new_convo)
            session.commit()
            session.refresh(new_convo)
        return new_convo

    @on(ChapterView.StartConversation)
    async def start_conversation(self, event: ChapterView.StartConversation) -> None:
        sender = event.sender
        sender.toc_address
        sender.book.id
        sender.chapter_content
        new_convo = self._create_conversation(sender.toc_address)

        chat_area_switcher = self.query_one("#chat_area_switcher", ContentSwitcher)
        chat_list = self.query_one("#chat_list", ChatList)
        chat_widget = ChatFlowWidget(
            book=self.book,
            toc_address=new_convo.toc_address,
            convo_id=new_convo.id,
            convo_content=new_convo.content,
        )
        chat_widget.chapter_content = sender.chapter_content
        widget_id = chat_widget.widget_id
        await chat_area_switcher.add_content(chat_widget, id=widget_id)
        await chat_list.insert_chat_list_item(
            convo=new_convo, toc_address=sender.toc_address
        )

        await chat_widget.chat_started(new_convo)

    def action_book_list(self) -> None:
        """Action to go back to the book list screen."""
        self.app.pop_screen()
