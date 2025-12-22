from __future__ import annotations
from dataclasses import dataclass
import asyncio
import random
from langchain_core.runnables import Runnable

from typing import Any, Dict, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import AsyncIterator, Dict, Iterator, Optional

# If you prefer the legacy import paths, keep it modern:
from langchain_openai import ChatOpenAI

PROMPT_TEXT = """you are a highly qualified Specialist and currently writing the following book: {book_title}.
Your task is to generate the chapter titled {chapter_title}. that will include in this book.
Table of contents of the book is as follows:
{book_toc}

Please write the chapter content below,
making sure to cover all relevant points in about {chapter_length} words.

You write your answer in markdown format and never include "Heading" tags like #, ##, etc.
Just write the text directly.
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
    prompt = ChatPromptTemplate.from_template(PROMPT_TEXT)

    chain = prompt | llm | StrOutputParser()
    return chain


def invoke_chain(
    chain: Runnable,
    *,
    book_title: str,
    chapter_title: str,
    book_toc: str,
    chapter_length: int | str,
) -> AsyncIterator[str]:
    """
    Real invocation (calls the model).
    """
    payload = {
        "book_title": book_title,
        "chapter_title": chapter_title,
        "book_toc": book_toc,
        "chapter_length": chapter_length,
    }
    return chain.astream(payload)


async def dummy_astream(
    inputs: Dict[str, object],
    *,
    seed: int = 42,
    min_delay_s: float = 0.01,
    max_delay_s: float = 0.05,
    chunk_min_chars: int = 12,
    chunk_max_chars: int = 48,
) -> AsyncIterator[str]:
    """
    Async streaming dummy that matches a typical LangChain astream() surface:
        async for chunk in chain.astream(inputs):
            ...

    It yields text chunks (strings) over time, simulating LLM streaming cadence.
    """
    rng = random.Random(seed)

    book_title = str(inputs.get("book_title", "Untitled Book"))
    chapter_title = str(inputs.get("chapter_title", "Untitled Chapter"))
    book_toc = str(inputs.get("book_toc", "")).strip()
    chapter_length_raw: int = int(inputs.get("chapter_length", 900))  # type: ignore

    try:
        target_words = int(chapter_length_raw)  # rough target
    except Exception:
        target_words = 900

    # LLM-ish text with no markdown heading tags.
    base_text = (
        f"You are writing a chapter for the book “{book_title}”, focused on “{chapter_title}”.\n\n"
        f"The table of contents frames the context:\n"
        f"{book_toc}\n\n"
        f"This chapter targets about {target_words} words, so it should stay practical and direct. "
        f"Start with scope and assumptions, then provide a workflow the reader can reuse, and end with a checklist.\n\n"
        f"A reliable workflow is: define intent, constrain format, provide enough context, and verify the output shape. "
        f"When prompt variables are explicit, the output is more consistent and easier to validate.\n\n"
        f"As you stream output to a UI, focus on incremental rendering: append-only updates, stable whitespace, "
        f"and graceful handling of partial chunks. Good streaming feels smooth even when chunk sizes vary.\n\n"
        f"Wrap up with a short recap and an action list so readers can immediately apply the chapter’s guidance."
    )

    # Pad to approximate target length (simple + deterministic).
    words = base_text.split(sep=" ")
    if len(words) < target_words:
        filler = [
            "Keep paragraphs short so the reader can scan while the text arrives.",
            "Test with long TOCs, unusual punctuation, and extra whitespace to harden your UI.",
            "Vary chunk sizes to expose reflow issues and ensure cursor placement is stable.",
            "Ensure your renderer preserves line breaks and doesn’t introduce heading tags.",
            "A final checklist helps confirm the prompt produced the intended structure.",
        ]
        i = 0
        while len(words) < target_words:
            words.extend(filler[i % len(filler)].split())
            i += 1

    text = " ".join(words)

    # Yield chunks with async delays.
    idx = 0
    n = len(text)
    while idx < n:
        chunk_size = rng.randint(chunk_min_chars, chunk_max_chars)
        chunk = text[idx : idx + chunk_size]
        idx += chunk_size

        await asyncio.sleep(rng.uniform(min_delay_s, max_delay_s))
        yield chunk


# --- Optional: a minimal wrapper that looks like a LangChain Runnable ---
class DummyStreamingRunnable:
    """
    Drop-in-ish object exposing .astream(inputs) for your UI tests.
    (So you can swap it for the real chain without changing calling code.)
    """

    def __init__(
        self,
        *,
        seed: int = 42,
        min_delay_s: float = 0.01,
        max_delay_s: float = 0.05,
        chunk_min_chars: int = 12,
        chunk_max_chars: int = 48,
    ):
        self.seed = seed
        self.min_delay_s = min_delay_s
        self.max_delay_s = max_delay_s
        self.chunk_min_chars = chunk_min_chars
        self.chunk_max_chars = chunk_max_chars

    async def astream(self, inputs: ChapterInputs) -> AsyncIterator[str]:
        async for chunk in dummy_astream(
            inputs.to_dict(),
            seed=self.seed,
            min_delay_s=self.min_delay_s,
            max_delay_s=self.max_delay_s,
            chunk_min_chars=self.chunk_min_chars,
            chunk_max_chars=self.chunk_max_chars,
        ):
            yield chunk


# --- Demo ---
async def _demo():
    dummy_chain = DummyStreamingRunnable(min_delay_s=0.02, max_delay_s=0.08)

    typed_inputs = ChapterInputs(
        book_title="The Pragmatic AI Writer",
        chapter_title="Prompt Engineering for Consistent Chapters",
        book_toc="1. Foundations\n2. Context\n3. Prompts\n4. Editing",
        chapter_length=250,
    )
    print("Generating chapter content...\n")
    async for chunk in dummy_chain.astream(typed_inputs):
        print(chunk, end="", flush=True)
    print("\n\n[done]")


if __name__ == "__main__":
    asyncio.run(_demo())
