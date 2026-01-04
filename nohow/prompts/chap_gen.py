from __future__ import annotations
from dataclasses import dataclass
import asyncio
import random
from langchain_core.runnables import Runnable

from typing import Any, Dict, Optional

from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_core.output_parsers import StrOutputParser
from typing import AsyncIterator, Dict, Iterator, Optional

# If you prefer the legacy import paths, keep it modern:
from langchain_openai import ChatOpenAI

SYSTEM_TEXT = """You are a highly qualified subject-matter specialist and professional book author.

Follow these rules strictly:
- Write in Markdown format.
- Do NOT use heading tags such as #, ##, ###, or similar.
- Respond ONLY with the chapter content. Do not add explanations, introductions, or commentary.
- Maintain a professional, well-structured, book-quality writing style.
- Ensure clarity, coherence, and logical flow.
"""


PROMPT_TEXT = """You are writing a book titled "{book_title}".

Generate the chapter titled "{chapter_title}" based on the following table of contents:

{book_toc}

Requirements:
- Cover all relevant points implied by the chapter title and table of contents.
- Target length: approximately {chapter_length} words.

"""


@dataclass(frozen=True, slots=True)
class ChapterInputs:
    book_title: str
    chapter_title: str
    book_toc: str
    chapter_length: int  # keep it int: less ambiguity than int|str

    def to_dict(self) -> dict[str, object]:
        return {
            "book_title": self.book_title,
            "chapter_title": self.chapter_title,
            "book_toc": self.book_toc,
            "chapter_length": self.chapter_length,
        }


def build_chain(
    llm: ChatOpenAI,
) -> Runnable:
    """
    Build and return a runnable chain:
      inputs (dict) -> formatted prompt -> OpenAI chat model -> string output
    """

    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessagePromptTemplate.from_template(SYSTEM_TEXT),
            HumanMessagePromptTemplate.from_template(PROMPT_TEXT),
        ]
    )
    chain = prompt | llm | StrOutputParser()
    return chain


def invoke_chain(
    chain: Runnable,
    inputs: ChapterInputs,
) -> AsyncIterator[str]:
    """
    Real invocation (calls the model).
    """
    return chain.astream(inputs.to_dict())


async def _demo() -> None:
    """Demo function to illustrate usage."""
    llm = ChatOpenAI(
        model_name="gpt-3.5-turbo",
        temperature=0.7,
        streaming=True,
    )
    chain = build_chain(llm)

    inputs = ChapterInputs(
        book_title="The Art of Programming",
        chapter_title="Chapter 3: Data Structures",
        book_toc="- Chapter 1: Introduction\n- Chapter 2: Algorithms\n- Chapter 3: Data Structures\n- Chapter 4: Advanced Topics",
        chapter_length=500,
    )

    print("Generating chapter content...\n")
    async for chunk in invoke_chain(chain, inputs):
        print(chunk, end="", flush=True)
    print("\n\nGeneration complete.")


if __name__ == "__main__":
    asyncio.run(_demo())
