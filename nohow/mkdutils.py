from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Sequence


@dataclass(slots=True)
class TocNode:
    """A node in a Markdown table-of-contents tree.

    - level: 1 for H1, 2 for H2, etc.
    - title: the heading text
    - line: 1-based line number where the heading was found (start line)
    - end_line: 1-based inclusive end line for the section covered by this heading
    - children: nested headings (e.g., H2 under an H1)
    """

    title: str
    level: int
    line: int
    end_line: int | None = None
    children: List["TocNode"] = field(default_factory=list)


def extract_toc_tree(markdown: str, *, min_level: int = 1, max_level: int = 6) -> List[TocNode]:
    """Extract a TOC tree from a Markdown string.

    This parses ATX-style headings only:
        # H1
        ## H2
        ### H3
        ...

    It ignores headings inside fenced code blocks.

    Args:
        markdown: Markdown source text.
        min_level: Minimum heading level to include (default 1).
        max_level: Maximum heading level to include (default 6).

    Returns:
        A list of top-level TocNode items (typically H1 nodes). Lower-level
        headings are nested under the nearest preceding parent heading.

    Notes:
        Each TocNode also gets an `end_line` computed as the last line belonging
        to that section. The end is determined by the next heading whose level
        is <= the current node's level (i.e., a sibling or an ancestor sibling).
        If no such heading exists, the end is the last line of the document.
    """
    if min_level < 1 or max_level > 6 or min_level > max_level:
        raise ValueError("min_level/max_level must satisfy 1 <= min_level <= max_level <= 6")

    total_lines = markdown.count("\n") + 1 if markdown else 0

    roots: List[TocNode] = []
    stack: List[TocNode] = []

    # Keep headings in document order so we can compute end_line ranges.
    ordered_nodes: List[TocNode] = []

    in_fenced_code = False
    fence: str | None = None  # "```" or "~~~"

    for line_no, raw_line in enumerate(markdown.splitlines(), start=1):
        line = raw_line.rstrip("\n")

        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = stripped[:3]
            if not in_fenced_code:
                in_fenced_code = True
                fence = marker
            else:
                if fence == marker:
                    in_fenced_code = False
                    fence = None
            continue

        if in_fenced_code:
            continue

        # ATX heading: up to 3 leading spaces, then 1-6 #'s, then space or end.
        # We accept "###Title" as well (common in the wild), but prefer trimming.
        s = line
        if len(s) - len(s.lstrip(" ")) > 3:
            continue
        s = s.lstrip(" ")
        if not s.startswith("#"):
            continue

        level = 0
        for ch in s:
            if ch == "#":
                level += 1
            else:
                break

        if level < min_level or level > max_level:
            continue

        rest = s[level:].strip()
        if not rest:
            continue

        # Remove optional closing #'s: "## Title ##"
        rest = rest.rstrip()
        i = len(rest) - 1
        while i >= 0 and rest[i] == "#":
            i -= 1
        if i < len(rest) - 1:
            rest = rest[: i + 1].rstrip()

        title = rest
        node = TocNode(title=title, level=level, line=line_no, end_line=None)
        ordered_nodes.append(node)

        # Pop until we find a parent with lower level.
        while stack and stack[-1].level >= level:
            stack.pop()

        if not stack:
            roots.append(node)
        else:
            stack[-1].children.append(node)

        stack.append(node)

    # Compute end_line for each node based on the next heading with level <= current.level.
    # end_line is inclusive and is set to (next_heading.line - 1). If none, last doc line.
    if total_lines == 0:
        return roots

    for idx, node in enumerate(ordered_nodes):
        end = total_lines
        for nxt in ordered_nodes[idx + 1 :]:
            if nxt.level <= node.level:
                end = max(node.line, nxt.line - 1)
                break
        node.end_line = end

    return roots


def flatten_toc(toc: Sequence[TocNode]) -> List[tuple[int, str, int, int]]:
    """Flatten a TOC tree into a list of (level, title, start_line, end_line) tuples (preorder)."""
    out: List[tuple[int, str, int, int]] = []

    def walk(nodes: Sequence[TocNode]) -> None:
        for n in nodes:
            if n.end_line is None:
                raise ValueError("TocNode.end_line is not set. Did you build the TOC via extract_toc_tree()?")
            out.append((n.level, n.title, n.line, n.end_line))
            walk(n.children)

    walk(toc)
    return out
