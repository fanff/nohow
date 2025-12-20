from nohow.mkdutils import extract_toc_tree, flatten_toc


def test_flatten_toc_nested_headings() -> None:
    md = """
# Book Title

Some intro text.

## Chapter 1
### Section 1.1
### Section 1.2

## Chapter 2
### Section 2.1

# Appendix
## Notes
""".lstrip()

    toc = extract_toc_tree(md)
    flat = flatten_toc(toc)

    assert flat == [
        (1, "Book Title"),
        (2, "Chapter 1"),
        (3, "Section 1.1"),
        (3, "Section 1.2"),
        (2, "Chapter 2"),
        (3, "Section 2.1"),
        (1, "Appendix"),
        (2, "Notes"),
    ]


def test_extract_toc_ignores_fenced_code_blocks() -> None:
    md = """
# Real Title

