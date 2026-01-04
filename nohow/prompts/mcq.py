from typing import List, Set
from pydantic import BaseModel, Field, conlist, field_validator, conset
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser, StrOutputParser
from langchain_openai import ChatOpenAI

import json


your_chapter_text = """
You are a helpful assistant.
You speak naturally in a chat and express yourself in markdown. 

You are a specialized and qualified book Author and you wrote the following 
chapter of your book:

**Comprehensions and readable code.**

Comprehensions are one of Python's most expressive constructs: compact, often faster than equivalent loops, and naturally suited to mapping, filtering, and simple transformations. But expressiveness must be tempered by readability. This chapter shows how to use list, set, dict and generator comprehensions idiomatically, when to prefer alternatives, and how to keep comprehensions clear and maintainable.

**Why use comprehensions**

Comprehensions capture a common pattern: produce a new sequence by transforming or selecting elements from an iterable. They are preferable to repeated append operations because they state intent directly — "build this list" — and avoid boilerplate.

Example: create a list of squared numbers from a sequence.

```
squares = [x*x for x in numbers]
```

This is shorter and more immediately clear than the loop equivalent:

```
squares = []
for x in numbers:
    squares.append(x * x)
```

Comprehensions are compiled to efficient bytecode and, for many simple transformations, run faster than explicit loops in CPython. For large datasets, generator expressions provide memory efficiency by generating values lazily.

**Types of comprehensions**

- List comprehension: [expr for item in iterable if condition]
- Set comprehension: {expr for item in iterable if condition}
- Dict comprehension: {key_expr: value_expr for item in iterable if condition}
- Generator expression: (expr for item in iterable if condition)

Examples:

```
unique_lengths = {len(s) for s in strings}
mapping = {name: age for name, age in pairs if age >= 18}
evens = (x for x in range(1000000) if x % 2 == 0)
```

Use the type of comprehension that matches your needs. Prefer generator expressions when you do not need to store all results.

**Filtering and conditional expressions**

A comprehension can include an if filter to select items. If you need a conditional value transformation, use the conditional expression inside the result expression.

```
# filter:
positives = [x for x in numbers if x > 0]

# conditional expression in output:
signs = [("+" if x > 0 else "-" if x < 0 else "0") for x in numbers]
```

Avoid placing complex logic inside these expressions. If the conditional becomes long or has multiple branches, extract it to a helper function for clarity.

**Nested comprehensions and multiple iterables**

Comprehensions support multiple for-clauses, which read in the same order as equivalent nested loops.

```
pairs = [(x, y) for x in xs for y in ys]
flattened = [elem for row in matrix for elem in row]
```

While concise, nested comprehensions can become hard to understand as nesting depth grows. For deeply nested logic, prefer explicit loops or use itertools utilities (product, chain, combinations) with descriptive variable names.

**Readability rules and style**

Clarity is the primary goal. Use these pragmatic rules:

- Keep comprehension expressions simple. If the expression requires several operations or nested conditionals, move them into a named helper function.
- Avoid comprehensions with more than two for-clauses or complicated if clauses. Prefer a loop when complexity grows.
- Don't use comprehensions for side effects. Comprehensions are intended to build collections; using them only to execute a function for its side effects (e.g., printing, mutating external state) is poor style. Use a for-loop instead.
- Give meaningful variable names. Avoid one-letter names except for small, well-understood scopes like indices.
- Break long comprehensions across multiple lines using parentheses and align the for-clauses for readability:

```
result = [
    process(x)
    for x in items
    if condition(x)
]
```

Follow PEP 8 line-length and indentation guidance when formatting comprehensions.

**Comprehension vs map/filter**

List comprehensions are often more readable than map() and filter(), especially with lambda functions:

```
# less readable
doubled = list(map(lambda x: x*2, data))

# clearer
doubled = [x*2 for x in data]
```

Use map when applying a simple named function and you want minor performance or to compose pipelines. Prefer comprehensions for clarity when transformation logic is non-trivial.

**Generators and memory**

Generator expressions are ideal when you want an iterator rather than an in-memory list. They save memory for large datasets and integrate with functions that consume iterables (sum, any, all, sorted).

```
# lazy
total = sum(x*x for x in large_sequence)
```

Be mindful that a generator can only be iterated once. If you need to traverse results multiple times, materialize to a list.

**Common pitfalls**

- Late binding in lambdas inside comprehensions: when creating closures, loop variables may be captured by reference. Avoid surprises by using default arguments.

```
# problem: all functions will use the final value of i
funcs = [lambda: i for i in range(3)]

# fix:
funcs = [lambda i=i: i for i in range(3)]
```

- Using comprehensions for side effects, as noted above. Example to avoid:

```
# bad
[_do_something(x) for x in items]  # returns a list of None, but side effects are intended

# good
for x in items:
    _do_something(x)
```

- Overly complex nested comprehensions make debugging and understanding code harder than a few more lines with explicit loops and comments.

- Mutable defaults and comprehension interactions: comprehension expressions that build lists of mutable objects are fine, but be conscious when you reuse references.

**When to prefer explicit loops**

Comprehensions should be used when they increase clarity and conciseness. Use explicit loops when:

- The transformation includes multiple statements or mutation.
- You need explicit error handling or logging in the loop.
- Side effects are central to the operation.
- There are many nested loops or complex filtering logic.

A clear loop is often easier for future maintainers to understand than an obscure one-liner.

**Using standard library helpers**

The itertools module complements comprehensions, offering tools that keep code readable and efficient:

- itertools.chain.from_iterable for flattening instead of nested comprehensions when clarity is improved.
- itertools.product and combinations for Cartesian products and combinations with readable intent.

Example: flattening

```
from itertools import chain
flattened = list(chain.from_iterable(matrix))
```

This is sometimes clearer than a nested comprehension, especially when the intent is to flatten rather than to express nested iteration.

**Testing and types**

Comprehensions can benefit from type hints and small unit tests. While you cannot annotate the comprehension itself, annotate the variable to document the expected type.

```
from typing import List

squares: List[int] = [x*x for x in numbers]
```

Unit tests that exercise comprehension results guard against regressions when comprehension logic becomes more complex.

**Summary**

Comprehensions are powerful and elegant when used for straightforward transformations and filters. Favor them for their clarity and brevity, but respect the trade-off between concision and understandability. When comprehension expressions start to grow — with nested loops, complex conditionals, or side effects — prefer explicit loops, helper functions, or itertools utilities. Use descriptive names, break long comprehensions across lines, avoid side effects, and choose generator expressions to conserve memory. The most readable code communicates intent with minimal cognitive load; use comprehensions as tools toward that goal, not as an end in itself.

Now your task is to help the user with their requests about this chapter.
Answer user questions, provide explanation and help user understand your chapter content.
"""


class MCQGen(BaseModel):
    question: str = Field(..., min_length=5)
    choices: conlist(str, min_length=2, max_length=4)  # 2..4 choices
    correct_answers: conlist(int, min_length=1)  # at least 1 index

    @field_validator("correct_answers")
    @classmethod
    def validate_correct_indices(cls, v, info):
        # choices are not directly available here in Pydantic v2 validators unless using model_validator.
        # We'll validate indices at the wrapper level below, or use a model_validator.
        return v


def gen_mcqs_from_chain_result(result: str) -> List[MCQGen]:
    try:
        res = json.loads(result)  # validate JSON structure
    except json.JSONDecodeError as e:
        return []
    else:
        res_list = res["items"] if "items" in res else res  # handle direct list

        return [MCQGen(**item) for item in res_list]


class MCQGenList(BaseModel):
    items: List[MCQGen] = Field(..., min_length=1)


class MCQForm(BaseModel):
    items: List[MCQGen] = Field(..., min_length=1)
    user_answers: List[List[int]] = Field(...)

    def score(self) -> float:
        """Score the user's answers succes rate between 0 and 1."""
        if len(self.items) != len(self.user_answers):
            # assume no answer for missing user answers
            ua = self.user_answers + [[]] * (len(self.items) - len(self.user_answers))
        else:
            ua = self.user_answers

        correct_count = 0
        for mcq, user_ans in zip(self.items, ua):
            if set(mcq.correct_answers) == user_ans:
                correct_count += 1

        score_ratio = correct_count / len(self.items)
        return score_ratio


SYSTEM_TEXT = """You generate multiple-choice questions (MCQs) from provided chapter content.

Output rules (STRICT):
- Output ONLY a JSON array of objects.
- Each object MUST have exactly these keys: "question", "choices", "correct_answers".

Field rules:
- "question":
  - A clear, standalone question.
  - MAY include Markdown (inline or block) and math expressions (e.g., LaTeX-style $...$).
  - MAY include fenced code blocks if needed.
- "choices":
  - An array of 2 to 4 answer choice strings (max 4).
  - Keep choices simple, concise, and plain-text.
  - Do NOT include code blocks, markdown formatting, or math expressions in choices unless strictly necessary.
- "correct_answers":
  - An array of integers representing 0-based indices into "choices".
  - Include at least 1 correct answer index.
  - Use multiple correct answers only when conceptually required.

Global constraints:
- Do not add any other keys.
- Do not include commentary, markdown outside string values, or code fences wrapping the JSON.
- Do not invent facts not supported by the chapter.
"""

PROMPT_TEXT = """
Create {num_questions} MCQs based ONLY on the chapter content below.

Guidelines:
- Questions should cover key concepts, definitions, cause/effect, and practical implications.
- Avoid trivial wording and avoid "All of the above"/"None of the above".
- Keep each choice concise and unambiguous.
- Use up to 4 choices per question (2-4).

Chapter content:
{chapter_content}

{format_instructions}

"""

PROMPT_TEXT_WITH_EXCLUSION = """
Create {num_questions} NEW MCQs based ONLY on the chapter content below.

Hard constraints:
- Do NOT repeat any question from the Existing questions list.
- Do NOT create near-duplicates (same concept/tested point with only minor rewording).
- If an Existing question already covers a concept, choose a different concept from the chapter.
- If you cannot produce {num_questions} truly non-overlapping questions, produce fewer rather than repeating.

Quality guidelines:
- Cover key concepts, definitions, cause/effect, and practical implications.
- Mix difficulty (some recall, some application).
- Avoid trivial wording and avoid "All of the above"/"None of the above".
- Keep each choice concise and unambiguous.
- Use 2 to 4 choices per question (max 4).
- correct_answers must be 0-based indices into choices.

Existing questions (do not repeat these, and avoid near-duplicates):
{existing_questions}

Chapter content:
{chapter_content}

{format_instructions}
"""


def generate_mcqs_from_chapter(
    llm, chapter_text: str, total_count: int, generate_by: int = 3
) -> List[MCQGen]:
    parser = PydanticOutputParser(pydantic_object=MCQGenList)
    out_instr = parser.get_format_instructions()

    all_mcqs: List[MCQGen] = []

    while len(all_mcqs) < total_count:
        # print(f"Generating MCQ batch {batch_idx+1}/{batch_count}...")
        if not all_mcqs:
            prompt = (
                ChatPromptTemplate.from_messages(
                    [
                        ("system", SYSTEM_TEXT),
                        ("human", PROMPT_TEXT),
                    ]
                )
                .partial(format_instructions=out_instr)
                .partial(num_questions=generate_by)
            )
        else:
            # prepare existing questions list
            existing_questions = "\n".join(f"- {mcq.question}" for mcq in all_mcqs)
            prompt = (
                ChatPromptTemplate.from_messages(
                    [
                        ("system", SYSTEM_TEXT),
                        ("human", PROMPT_TEXT_WITH_EXCLUSION),
                    ]
                )
                .partial(format_instructions=out_instr)
                .partial(num_questions=min(generate_by, total_count - len(all_mcqs)))
                .partial(existing_questions=existing_questions)
            )

        chain = prompt | llm | StrOutputParser()
        result = chain.invoke({"chapter_content": chapter_text})
        mcqs = gen_mcqs_from_chain_result(result)
        all_mcqs.extend(mcqs)
    return all_mcqs


async def demo():

    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.9,
        api_key="",
    )  # pick your model
    mcqs = generate_mcqs_from_chapter(
        llm=llm, chapter_text=your_chapter_text, total_count=5, generate_by=3
    )
    for idx, mcq in enumerate(mcqs):
        print(f"Q{idx+1}: {mcq.question}")
        for cidx, choice in enumerate(mcq.choices):
            print(f"  {cidx}. {choice}")
        print(f"  Correct answers: {mcq.correct_answers}")
        print()

    form = MCQForm(
        items=mcqs,
        user_answers=[],
    )

    print(form.score())
    json_str = form.model_dump_json()

    print("Serialized MCQForm:")
    print(json_str)
    with open("mcq_form.json", "w", encoding="utf-8") as f:
        f.write(json_str)


if __name__ == "__main__":
    import asyncio

    asyncio.run(demo())
