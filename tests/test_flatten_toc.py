import json
from nohow.mkdutils import _extract_toc_, flatten_toc, to_tree, TocTreeNode


def test_extract_and_flatten_toc_basic() -> None:
    md = """
# Title
## A
### A.1
## B
# End
blabla bla
""".lstrip()

    toc = _extract_toc_(md)
    toctree = to_tree(toc)  # just to check it doesn't crash*
    tree_dic = toctree.to_json()
    tree_json = json.dumps(tree_dic)  # just to check it doesn't crash**
    reloaded = TocTreeNode.from_json(
        json.loads(tree_json)
    )  # just to check it doesn't crash***

    assert reloaded.topology_signature() == toctree.topology_signature()
    assert reloaded.topology_sexpr() == toctree.topology_sexpr()
    assert flatten_toc(toc) == [
        (1, "Title", 1, 4),
        (2, "A", 2, 3),
        (3, "A.1", 3, 3),
        (2, "B", 4, 4),
        (1, "End", 5, 7),
    ]


def test_extract_toc_ignores_fenced_code_blocks() -> None:
    md = """
# Real
## Also Real
```markdown
### Also not a title
```
## Also Real
""".lstrip()

    toc = _extract_toc_(md)
    assert flatten_toc(toc) == [
        (1, "Real"),
        (2, "Also Real"),
        (2, "Also Real"),
    ]
