from __future__ import annotations
from langchain.messages import AnyMessage, HumanMessage, AIMessage, SystemMessage

import asyncio
from dataclasses import dataclass, field
from typing import AsyncIterator, List, Optional

from langchain_openai import ChatOpenAI


@dataclass(slots=True)
class ChatSession:
    """
    Holds conversation state and exposes:
      - append_user(text): mutates conversation with HumanMessage
      - stream_assistant(): async generator of string chunks
        and finally appends AIMessage to conversation
    """

    llm: ChatOpenAI
    conversation: List[AnyMessage] = field(default_factory=list)

    def append_user(self, text: str) -> None:
        self.conversation.append(HumanMessage(content=text))

    async def stream_assistant(self) -> AsyncIterator[str]:
        """
        Streams the assistant reply based on current conversation state.
        At the end, appends the completed AIMessage to the conversation.
        """
        parts: list[str] = []

        # LangChain streaming: yields AIMessageChunk objects (usually),
        # but we only expose strings to the UI.
        async for chunk in self.llm.astream(self.conversation):
            # chunk is typically an AIMessageChunk; robustly extract text:
            text = getattr(chunk, "content", None)
            if not isinstance(text, str):
                # Some setups may yield dict-ish chunks; best-effort:
                text = str(chunk)

            if text:
                parts.append(text)
                yield text

        full = "".join(parts)
        self.conversation.append(AIMessage(content=full))

    async def send(self, user_text: str) -> AsyncIterator[str]:
        """
        Convenience: one call that appends the human message and streams the assistant.
        """
        self.append_user(user_text)
        async for token in self.stream_assistant():
            yield token

    def serialize_conversation(self) -> List[dict[str, str]]:
        """Serialize the conversation to a list of dicts for storage or transmission."""
        serialized = []
        for message in self.conversation:
            if isinstance(message, SystemMessage):
                role = "system"
            elif isinstance(message, HumanMessage):
                role = "user"
            elif isinstance(message, AIMessage):
                role = "assistant"
            else:
                role = "unknown"
            serialized.append({"role": role, "content": message.content})
        return serialized

    @staticmethod
    def create_from_serialized(llm, serialized: List[dict[str, str]]) -> ChatSession:
        """Create a ChatSession from a serialized list of dicts."""
        session = ChatSession(llm=llm)
        session.conversation = ChatSession.unserialize_conversation(serialized)
        return session

    @staticmethod
    def unserialize_conversation(serialized: List[dict[str, str]]) -> List[AnyMessage]:
        """Deserialize a list of dicts back into a list of BaseMessage objects."""
        conversation = []
        for item in serialized:
            role = item.get("role")
            content = item.get("content", "")
            if role == "system":
                conversation.append(SystemMessage(content=content))
            elif role == "user":
                conversation.append(HumanMessage(content=content))
            elif role == "assistant":
                conversation.append(AIMessage(content=content))
            else:
                # Unknown role; skip or handle as needed
                continue
        return conversation


def make_chat_session(llm: ChatOpenAI, chapter_content: str) -> ChatSession:

    session = ChatSession(llm=llm)

    # format the Default System message
    formatted_system = DEFAULT_SYSTEM_TEMPLATE.format(chapter_content=chapter_content)
    # seed the system message
    session.conversation.append(SystemMessage(content=formatted_system))
    return session


# --- Example system seed (system + your "prompting style") ---
DEFAULT_SYSTEM_TEMPLATE = """You are a helpful assistant.
You speak naturally in a chat and express yourself in markdown. 

You are a specialized and qualified book Author and you wrote the following 
chapter of your book:

{chapter_content}

Now your task is to help the user with their requests about this chapter.
Answer user questions, provide explanation and help user understand your chapter content.
"""


# --- Demo ---
async def _demo():
    session = make_chat_session(
        model_name="gpt-3.5-turbo",
        system_message=DEFAULT_SYSTEM,
        temperature=0.4,
    )

    # Optional: preseed additional context (your “prompt”)
    session.conversation.append(
        HumanMessage(
            content="We are writing a book together. Keep responses practical."
        )
    )

    async for chunk in session.send(
        "Help me design a chapter outline about prompt testing with streaming UIs."
    ):
        print(chunk, end="", flush=True)

    print("\n\n--- Conversation state now contains ---")
    for m in session.conversation:
        print(
            type(m).__name__,
            "=>",
            (m.content[:80] + "..." if len(m.content) > 80 else m.content),
        )


if __name__ == "__main__":
    asyncio.run(_demo())
