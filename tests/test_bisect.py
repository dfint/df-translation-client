import operator
import string
from functools import reduce
from typing import List

import pytest

from df_translation_client.widgets.bisect_tool import Node


@pytest.mark.parametrize("data", [
    list(string.ascii_letters[:10]),
    list(string.ascii_letters[:7]),
    ["test"],
    ["test1", "test2"],
])
def test_node(data):
    node = Node(data)
    assert node.size == len(data)
    assert node.start == 0 and node.end == len(data) - 1
    if len(data) == 1:
        assert node.tree_text == f"[{node.start} : {node.end}] ({node.end - node.start + 1} string)"
        assert node.column_text == f"{data[0]!r}"
    elif len(data) == 2:
        assert node.tree_text == f"[{node.start} : {node.end}] ({node.end - node.start + 1} strings)"
        assert node.column_text == ",".join(map(repr, data))
    else:
        assert node.tree_text == f"[{node.start} : {node.end}] ({node.end - node.start + 1} strings)"
        assert node.column_text == f"{data[node.start]!r} ... {data[node.end]!r}"


@pytest.mark.parametrize("data", [
    list(string.ascii_letters[:7]),
    list(string.ascii_letters[:10]),
])
def test_split(data: List):
    node = Node(data)
    children = node.split()

    if len(data) % 2 == 0:
        assert children[0].size == children[1].size == len(data) // 2
    else:
        assert children[0].size == len(data) // 2 + 1
        assert children[1].size == len(data) // 2

    assert sum(node.size for node in children) == len(data)
    assert reduce(operator.add, (list(node.items) for node in children), []) == data
