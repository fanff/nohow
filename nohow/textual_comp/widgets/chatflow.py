import asyncio
from nohow.prompts.chat_gen import ChatSession, make_chat_session
from langchain.messages import HumanMessage, AIMessage
from nohow.prompts.chap_gen import ChapterInputs, DummyStreamingRunnable, build_chain
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
from nohow.db.utils import get_session, setup_database
from nohow.textual_comp.widgets.chatbox import ChatInputArea, ChatMessage
from shortuuid import ShortUUID


class IsTyping(Horizontal):
    DEFAULT_CSS = """
    IsTyping {
        height: 1;
        }
    """

    def compose(self) -> ComposeResult:
        yield LoadingIndicator()
        yield Label("  AI is responding ")


class ChatFlowWidget(Widget):
    """Widget representing a chat flow for a book."""

    BINDINGS = [
        Binding(
            key="g",
            action="last_message",
            description="Focus Last Message",
            key_display="^d",
        ),
        Binding(
            key="i",
            action="focus('chat_input_area')",
            description="Focus Input",
            key_display="i",
        ),
        Binding(
            key="ctrl+u",
            action="scroll_page_convo(True)",
            description="Page Up",
            key_display="^u",
        ),
        Binding(
            key="ctrl+d",
            action="scroll_page_convo(False)",
            description="Page Down",
            key_display="^d",
        ),
        Binding("k", "scroll_convo(True)", "Scroll Up", show=False),
        Binding("j", "scroll_convo(False)", "Scroll Down", show=False),
    ]

    DEFAULT_CSS = """
    ChatFlowWidget {
        
        padding: 1 1;
        height: 1fr;
    }

    #chat-input-text-container {
        height: 10;
        padding: 1 1;
    }

    #chat-scroll-container {
        height: 1fr;
        padding: 1 1;
    }
    
    """

    def __init__(
        self, book: Book, toc_address: str, convo_id: int, convo_content: str, **kwargs
    ) -> None:
        super().__init__(**kwargs)
        self.book_id: int = book.id
        self.book: Book = book
        self.convo_id = convo_id
        self.convo_content = convo_content

        # a string representing toc_address
        self.toc_address = toc_address

        self.chapter_content: str = ""

        # for managing the conversation
        self.allow_input_submit = True
        self.responding_indicator = IsTyping()
        self.responding_indicator.display = False
        llm = self.app.app_context.llm
        assert llm is not None
        if convo_content:
            self.chat_session = ChatSession.create_from_serialized(
                llm=llm,
                serialized=json.loads(convo_content),
            )
        else:
            self.chat_session = None

    @property
    def widget_id(self):
        return f"convo_{self.toc_address.replace('.', '_')}" + str(self.convo_id)

    async def chat_started(self, convo: Convo) -> None:
        if self.chat_session is not None:
            return

        llm = self.app.app_context.llm
        assert llm is not None

        # 1. prepare inputs for the chat sessions creation
        self.chapter_content

        self.chat_session = make_chat_session(
            llm=llm, chapter_content=self.chapter_content
        )
        update_convo_content(
            convo_id=self.convo_id,
            new_content=json.dumps(self.chat_session.serialize_conversation()),
        )

        for message in self.chat_session.conversation:
            chat_box = ChatMessage(message=message, model_name="")
            await self.chat_container.mount(chat_box)

    def compose(self):
        yield Static(f"chapter : {self.toc_address} , bookid: {self.book_id} ")
        yield Static(f"Conversation ID: {self.convo_id}")
        # yield Static(f"Conversation Content: {self.convo_content}")
        # yield UserInputWidget(id="user_input_widget")
        with VerticalScroll(id="chat-scroll-container") as vertical_scroll:
            self.chat_container = vertical_scroll
            vertical_scroll.can_focus = False

            if self.chat_session is not None:
                for message in self.chat_session.conversation:
                    chat_box = ChatMessage(message=message, model_name="dummy-model")
                    yield chat_box
        with Horizontal(id="chat-input-text-container"):
            self.input_area = ChatInputArea(self, id="chat_input_area")
            yield self.input_area
            yield Button("Send", id="btn-submit")
        yield self.responding_indicator

    def scroll_to_latest_message(self) -> None:
        """Scroll to the latest message in the chat flow."""
        if self.chat_container is not None:
            self.chat_container.refresh()
            self.chat_container.scroll_end(animate=False)

    @on(Button.Pressed, selector="#btn-submit")
    def on_submit(self, event: Button.Pressed):
        event.stop()
        self.input_area.post_message(ChatInputArea.Submit(self.input_area))

    @on(ChatInputArea.Submit)
    async def user_chat_message_submitted(self, event: ChatInputArea.Submit) -> None:
        if self.allow_input_submit:
            user_message = event.input_area.text
            if len(user_message):
                event.input_area.clear()
                await self.chat(user_message)

    async def chat(self, content: str) -> None:

        await self.progress_conversation(content)

    async def progress_conversation(self, message: str) -> None:
        user_message_chatbox = ChatMessage(
            message=HumanMessage(content=message), model_name=""
        )

        assert self.chat_container is not None

        # include the user message
        await self.chat_container.mount(user_message_chatbox)
        assert self.chat_session is not None
        self.scroll_to_latest_message()
        # force a little "wait here "
        await asyncio.sleep(0.1)
        # prepare the streaming response

        # append the AI message box
        ai_message_chatbox = ChatMessage(
            message=AIMessage(content=""), model_name=self.app.app_context.model_name
        )
        await self.chat_container.mount(ai_message_chatbox)
        self.scroll_to_latest_message()

        self.responding_indicator.display = True
        self.allow_input_submit = False
        self.action_last_message()

        async def stream_in_background():
            assert self.chat_session is not None
            async for chunk in self.chat_session.send(message):

                if await ai_message_chatbox.feed_chunk(chunk):
                    self.action_last_message()

            await ai_message_chatbox.finalize_message()
            update_convo_content(
                convo_id=self.convo_id,
                new_content=json.dumps(self.chat_session.serialize_conversation()),
            )
            self.responding_indicator.display = False
            self.allow_input_submit = True
            self.action_last_message()

        self.run_worker(stream_in_background(), exclusive=True)

    def action_last_message(self) -> None:
        """Focus the last message of the chat"""
        self.chat_container.children[-1].focus()

    def action_scroll_convo(self, up: bool) -> None:
        """Scroll the chat conversation up or down."""
        if up:
            self.chat_container.scroll_up()
        else:
            self.chat_container.scroll_down()

    def action_scroll_page_convo(self, up: bool) -> None:
        """Scroll the chat conversation up or down by a page."""
        if up:
            self.chat_container.scroll_page_up()
        else:
            self.chat_container.scroll_page_down()


class ChapterView(Widget):

    DEFAULT_CSS = """
    ChapterView {
        
        height: 100%;
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

    @property
    def widget_id(self):
        return f"convo_{self.toc_address.replace('.', '_')}"

    def compose(self):
        with VerticalScroll():
            yield Static(
                f"{self.book.title} chapter : {self.toc_address} , bookid: {self.book_id} "
            )
            yield Static(f"TOC Title: {self.tocnode}")
            yield Static(f"Generation inputs:\n{self.get_chapter_inputs()}")
            yield Markdown(self.chapter_content, id="chapter_content_md")

            yield Button("Generate Chapter", id="generate_chap_button")

            yield Button("Start Conversation", id="start_convo_button")

    def book_extract(self) -> str:
        if self.book:
            return self.book.get_toc_extract(
                self.tocnode.start_line - 1, self.tocnode.end_line
            )
        return ""

    def get_chapter_inputs(self) -> ChapterInputs:
        return ChapterInputs(
            book_title=self.book.title,
            chapter_title=self.tocnode.title,
            book_toc=self.book_extract(),
            chapter_length=250,
        )

    @on(Button.Pressed, "#generate_chap_button")
    async def generate_chapter(self, event: Button.Pressed) -> None:
        event.stop()
        # 1. gather the inputs for generation
        chain = build_chain(self.app.app_context.llm)

        self.tocnode.title

        inputs = self.get_chapter_inputs()
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
        engine = setup_database()
        with get_session(engine) as session:
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

        new_chapter

    @on(Button.Pressed, "#start_convo_button")
    def start_conversation(self) -> None:
        event = self.StartConversation(self)
        self.post_message(event)


class UserInputWidget(Widget):
    """Widget representing user input area for chat."""

    DEFAULT_CSS = """
    UserInputWidget {
        border: solid green;
        padding: 1 1;
        height: auto;
    }
    UserInputWidget > Input {
        height: 3;
    }
    """

    def compose(self):
        yield Input(placeholder="Type your message here...", id="user_input_area")
        yield Button("Send", id="send_button", variant="primary")

    def on_mount(self) -> None:
        pass


class ChatListItem(ListItem):
    DEFAULT_CSS = """
    ChatListItem {
        height: auto;
        padding: 0 1;
        background: $surface;

        &.-h1 {
            color: $primary;
            text-style: bold underline;
        }
        &.-h2 {
            color: $primary 90% ;
            
        }

        &.-h3 {
            color: $primary 80% ;
        }

        &.-conversation {
            text-style: italic;
            color: $accent 90%;
        }
    }

    
    """

    def __init__(
        self,
        level: int,
        toc_index: str,
        chat_id: str,
        toc_title: str,
        is_open: bool = False,
    ) -> None:
        """
        Args:
            chat: The chat associated with this option.
            is_open: True if this is the chat that's currently open.
        """
        super().__init__()
        self.chat_id: str = chat_id
        self.is_open: bool = is_open
        self.toc_title: str = toc_title
        self.level: int = level
        self.toc_index: str = toc_index

    @property
    def is_title(self) -> bool:
        return self.chat_id == ""

    def compose(self) -> ComposeResult:
        if self.is_title:
            yield Static(f"{self.toc_index} {self.toc_title}")
        else:
            yield Static(f"[{self.chat_id}] ...")

    def on_mount(self) -> None:
        # Adjust padding based on level
        if self.is_title:
            padding_value = self.level * 2
            # add class based on level
            if self.level == 1:
                self.add_class("-h1")
            elif self.level == 2:
                self.add_class("-h2")
            else:
                self.add_class("-h3")
        else:
            self.add_class("-conversation")
            padding_value = (self.level * 2) + 2
        self.styles.padding = (0, 0, 0, padding_value)


class ChatList(Widget):
    DEFAULT_CSS = """
    ChatList {
        
        padding: 1 1;
        height: 100%;
        
    }
    """

    BINDINGS = [
        Binding(
            "i",
            action="focus('chat-input')",
            description="Focus Input",
            key_display="i",
        ),
        Binding("r", "rename_conversation", "Rename Chat", key_display="r"),
        Binding("d", "delete_conversation", "Delete Chat", key_display="d"),
        Binding("e", "export", "Export To Markdown", key_display="e"),
    ]
    COMPONENT_CLASSES = {"app-title", "app-subtitle"}

    current_chat_id: reactive[str | None] = reactive(None)
    current_book: Book | None = None
    all_convo: List[Convo]

    @dataclass
    class ChatOpened(Message):
        def __init__(self, item: ChatListItem) -> None:
            super().__init__()
            self.item = item

    def compose(self) -> ComposeResult:
        with Vertical(id="cl-header-container"):
            self.options = []
            self.option_list = ListView(
                *self.options,
                id="cl-option-list",
            )
            yield self.option_list

    def on_list_view_highlighted(self, event: ListView.Highlighted) -> None:
        item = event.item
        if isinstance(item, ChatListItem):
            self.current_chat_id = item.chat_id
            self.post_message(self.ChatOpened(item))
        event.stop()

    async def insert_chat_list_item(self, convo: Convo, toc_address: str):
        ol = self.query_one("#cl-option-list", ListView)
        insertion_index = 0
        level = 0
        for child_idx, child in enumerate(ol.children):
            assert isinstance(child, ChatListItem)
            if child.toc_index == toc_address:
                insertion_index = child_idx + 1
                level = child.level

        cli = ChatListItem(
            level=level,
            toc_index=str(convo.toc_address),
            chat_id=str(convo.id),
            toc_title="",
            is_open=False,
        )
        await ol.insert(insertion_index, [cli])
        ol.index = insertion_index

    def load_conversation_list_items(self):

        ol = self.query_one("#cl-option-list", ListView)
        ol.clear()
        if isinstance(self.current_book, Book) and isinstance(self.all_convo, list):
            if self.current_book.toc_tree:
                self.all_convo
                toc_tree = TocTreeNode.from_json(json.loads(self.current_book.toc_tree))
                for node in toc_tree.preorder():
                    convo_key = node.conversation_key()
                    matching_convos = [
                        c for c in self.all_convo if c.toc_address == convo_key
                    ]
                    ol.append(
                        ChatListItem(
                            level=node.level,
                            toc_index=convo_key,
                            chat_id="",
                            toc_title=node.title,
                            is_open=False,
                        )
                    )
                    for convo in matching_convos:
                        ol.append(
                            ChatListItem(
                                level=node.level + 1,
                                toc_index=convo.toc_address,
                                chat_id=str(convo.id),
                                toc_title=node.title,
                                is_open=False,
                            )
                        )
        else:
            return []
