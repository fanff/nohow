import asyncio
from nohow.prompts.chat_gen import ChatSession, make_chat_session
from langchain.messages import HumanMessage, AIMessage
from nohow.prompts.chap_gen import ChapterInputs, build_chain
from nohow.prompts.utils import new_message_of_type
from textual import on
from typing import List
import json
from nohow.mkdutils import TocTreeNode
from dataclasses import dataclass
from textual.widget import Widget
from textual.reactive import reactive
from textual.message import Message
from textual.widgets import (
    Static,
    TextArea,
    Button,
    Input,
    ListView,
    ListItem,
    Markdown,
)
from textual.events import Event, Click
from textual.widget import Widget
from textual.widgets import Button, OptionList, Static, LoadingIndicator, Label
from textual.widgets.option_list import Option
from textual.containers import Vertical, Horizontal, VerticalScroll
from textual.binding import Binding
from textual.app import ComposeResult

from rich.text import Text
from rich.console import RenderResult, Console, ConsoleOptions
from rich.style import Style
from rich.color import Color
from rich.padding import Padding
from rich.text import Text

from nohow.db.models import Book, Convo, Chapter, update_convo_content
from nohow.db.utils import get_session
from nohow.textual_comp.widgets.chatbox import ChatInputArea, ChatMessage
from shortuuid import ShortUUID

from nohow.textual_comp.widgets.utils import IsTyping


class ChapterView(Widget, can_focus=False, can_focus_children=True):

    DEFAULT_CSS = """
    ChapterView {
        height: 100%;
    }

    #chapter_content_area {
        border: blank $primary;
        &:focus {
            border: solid $accent;
            background: $boost;
        }
    }
    #chapter_content_md {
        
        margin: 1 10 1 7;
    }
    #chapter_buttons_area {
        height: auto;
        margin: 1 3 0 3;
    }
    #chapter_buttons_area_2 {
        height: auto;
        margin: 1 3 1 3;
    }
    
    """

    @dataclass
    class StartConversation(Message):
        def __init__(self, sender: "ChapterView") -> None:
            super().__init__()
            self.sender = sender

    def __init__(
        self,
        book: Book,
        tocnode: TocTreeNode,
        toc_address: str,
        chapter_content: str,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        self.book: Book = book
        self.book_id = book.id
        self.tocnode: TocTreeNode = tocnode
        # a string representing toc_address
        self.toc_address = toc_address

        self.chapter_content: str = chapter_content
        self.responding_indicator = IsTyping()
        self.responding_indicator.display = False

    @property
    def widget_id(self):
        return f"convo_{self.toc_address.replace('.', '_')}"

    def compose(self):
        yield self.responding_indicator
        with VerticalScroll(can_focus=True, id="chapter_content_area"):
            yield Markdown(self.chapter_content, id="chapter_content_md")

        with Horizontal(id="chapter_buttons_area"):
            yield Label("Chapter Length:")
            yield Button("250", compact=True, id="generate_chap_button_small")
            yield Button("500", compact=True, id="generate_chap_button_medium")
            yield Button("1000", compact=True, id="generate_chap_button_large")
            yield Button("2000", compact=True, id="generate_chap_button_xlarge")

        with Horizontal(id="chapter_buttons_area_2"):
            yield Button(
                "Start Conversation",
                compact=True,
                id="start_convo_button",
                variant="success",
            )
            yield Button(
                "Start Quiz", compact=True, id="start_quiz_button", variant="primary"
            )

    def book_extract(self) -> str:
        if self.book:
            return self.book.get_toc_extract(
                self.tocnode.start_line - 1, self.tocnode.end_line
            )
        return ""

    def get_chapter_inputs(self, chapter_length: int) -> ChapterInputs:
        # find the chapter length from the input

        return ChapterInputs(
            book_title=str(self.book.title),
            chapter_title=self.tocnode.title,
            book_toc=self.book_extract(),
            chapter_length=chapter_length,
        )

    @on(
        Button.Pressed,
        "#generate_chap_button_small, #generate_chap_button_medium, #generate_chap_button_large, #generate_chap_button_xlarge",
    )
    async def generate_chapter(self, event: Button.Pressed) -> None:
        event.stop()
        self.responding_indicator.display = True
        # 1. gather the inputs for generation
        chain = build_chain(self.app.app_context.llm)

        self.tocnode.title
        chapter_length_button_map = {
            "generate_chap_button_small": 250,
            "generate_chap_button_medium": 500,
            "generate_chap_button_large": 1000,
            "generate_chap_button_xlarge": 2000,
        }
        button_id = event.button.id
        chapter_length = chapter_length_button_map[button_id]

        inputs = self.get_chapter_inputs(chapter_length)
        # 1.1 grab the chapter content area
        chapter_content_md = self.query_one("#chapter_content_md", Markdown)
        # reset the content
        self.chapter_content = ""
        chapter_content_md.update("")

        # update function
        async def update_md_content(chunk: str) -> None:
            self.chapter_content += chunk
            await chapter_content_md.append(chunk)

        # 2. trigger generation process
        async for chunk in chain.astream(inputs.to_dict()):
            await update_md_content(chunk)

        # 3. finalize with saving to DB
        self.chapter_content
        self.book_id
        self.toc_address

        with get_session(self.app.get_db()) as session:
            # find if chapter already exists
            existing_chapter = (
                session.query(Chapter)
                .filter_by(toc_address=self.toc_address, book_id=self.book_id)
                .one_or_none()
            )
            if existing_chapter:
                existing_chapter.content = self.chapter_content
                session.commit()
                session.refresh(existing_chapter)
                new_chapter = existing_chapter
            else:
                new_chapter = Chapter(
                    content=self.chapter_content,
                    toc_address=self.toc_address,
                    book_id=self.book_id,
                )
                session.add(new_chapter)
                session.commit()
                session.refresh(new_chapter)

        self.responding_indicator.display = False

    @on(Button.Pressed, "#start_convo_button")
    def start_conversation(self) -> None:
        event = self.StartConversation(self)
        self.post_message(event)
