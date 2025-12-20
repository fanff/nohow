from nohow.mkdutils import extract_toc_tree, flatten_toc


def test_extract_and_flatten_toc_basic() -> None:
    md = """
# Title
## A
### A.1
## B
# End
""".lstrip()

    toc = extract_toc_tree(md)
    assert flatten_toc(toc) == [
        (1, "Title"),
        (2, "A"),
        (3, "A.1"),
        (2, "B"),
        (1, "End"),
    ]


def test_extract_toc_ignores_fenced_code_blocks() -> None:
    md = """
# Real

