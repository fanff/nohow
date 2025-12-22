from __future__ import annotations
import time


from nohow.prompts.utils import new_message_of_type
import pyperclip
from langchain.messages import AIMessage, HumanMessage, AnyMessage
import re
from nohow.utils import format_timestamp
from textual.binding import Binding
from textual.geometry import Size
from textual.widget import Widget
from textual.containers import Container
from textual.widgets import TextArea, Button, Markdown
from textual.message import Message
from textual import on, events


# from nohow.textual_comp.widgets.chatflow import ChatFlowWidget


class ChatInputArea(TextArea):
    BINDINGS = [
        Binding(
            key="ctrl+s",
            action="focus('cl-option-list')",
            description="Focus List",
            key_display="^s",
        ),
    ]

    class Submit(Message):
        def __init__(self, textarea: "ChatInputArea") -> None:
            super().__init__()
            self.input_area = textarea

        @property
        def control(self):
            return self.input_area

    def __init__(self, chat: "ChatFlowWidget", *args, **kwargs):
        super().__init__(*args, **kwargs)
        from nohow.textual_comp.widgets.chatflow import ChatFlowWidget

        self.chat: ChatFlowWidget = chat

    def _on_focus(self, event: events.Focus) -> None:
        super()._on_focus(event)
        self.chat.scroll_to_latest_message()


class ChatMessage(Widget, can_focus=True):
    BINDINGS = [
        Binding(
            key="ctrl+s",
            action="focus('cl-option-list')",
            description="Focus List",
            key_display="^s",
        ),
        Binding(
            key="i",
            action="focus('chat-input')",
            description="Focus Input",
            key_display="i",
        ),
        Binding(
            key="d", action="details", description="Message details", key_display="d"
        ),
        Binding(key="c", action="copy", description="Copy Message", key_display="c"),
        Binding(key="`", action="copy_code", description="Copy Code Blocks"),
    ]

    DEFAULT_CSS = """
    ChatMessage {
        padding: 1 1;
        border: none;
        width: 100%;
        height: auto;

        &:focus {
            outline-left: thick $primary;
            background: $boost;
        }
    }
    ChatMessage.human-message {
        background: $surface 10%;
        margin-left: 5;
    }
    ChatMessage.assistant-message {
        background: $accent 10%;
        margin-right: 5;
    }

    #message-markdown {
        width: 100%;
        height: auto;
    }
    """

    def __init__(
        self,
        *,
        model_name: str,
        message: AnyMessage,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
        )
        self._message = message

        self.model_name = model_name
        timestamp = format_timestamp(
            self.message.additional_kwargs.get("timestamp", 0) or 0
        )
        self.tooltip = f"Sent {timestamp}"

        self.chunk_buffer: str = ""
        self.last_debuff_time: float = 0.0

    @property
    def is_ai_message(self):
        return isinstance(self._message, AIMessage)

    def compose(self):
        self.markdown_widget = Markdown(
            self.message.content or "", id="message-markdown"
        )
        yield self.markdown_widget

    def on_mount(self) -> None:
        if self.is_ai_message:
            self.add_class("assistant-message")
        else:
            self.add_class("human-message")

    def get_code_blocks(self, markdown_string):
        pattern = r"```(.*?)\n(.*?)```"
        code_blocks = re.findall(pattern, markdown_string, re.DOTALL)
        return code_blocks

    def action_copy_code(self):
        codeblocks = self.get_code_blocks(self.message.content)
        output = ""
        if codeblocks:
            for lang, code in codeblocks:
                output += f"{code}\n\n"
            pyperclip.copy(output)
            self.notify("Codeblocks have been copied to clipboard", timeout=3)
        else:
            self.notify("There are no codeblocks in the message to copy", timeout=3)

    def action_copy(self) -> None:
        pyperclip.copy(self.message.content)
        self.notify("Message content has been copied to clipboard", timeout=3)

    def action_details(self) -> None:
        pass
        # self.app.push_screen(
        #    MessageInfo(message=self.message, model_name=self.model_name)
        # )

    def get_content_width(self, container: Size, viewport: Size) -> int:
        # Naive approach. Can sometimes look strange, but works well enough.
        content = self.message.content or ""
        return min(len(content), container.width)

    @property
    def message(self):
        return self._message

    async def feed_chunk(self, chunk: str) -> bool:
        """Feed a new chunk of text to the message content."""

        self.chunk_buffer += chunk
        now = time.time()
        if now - self.last_debuff_time > 0.2:
            await self.debuff()
            return True
        else:
            return False

    async def debuff(self) -> None:
        """Clear any buffered chunks without updating the message content."""
        current_content = self.message.content or ""
        updated_content = current_content + self.chunk_buffer
        self._message.content = updated_content
        await self.markdown_widget.append(self.chunk_buffer)
        self.chunk_buffer = ""
        self.last_debuff_time = time.time()
        self.refresh()

    async def finalize_message(self) -> None:
        """Finalize the message after all chunks have been fed."""
        # Any finalization logic can go here.
        if self.chunk_buffer:
            await self.debuff()
