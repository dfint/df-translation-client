import operator
from functools import reduce
from typing import List
from hypothesis import given, strategies as st

import pytest

from df_translation_client.widgets.bisect_tool import Node


@given(st.lists(st.text()))
def test_node(data):
    node = Node(data)
    assert node.size == len(data)
    assert node.start == 0 and node.end == len(data) - 1
    if len(data) == 0:
        assert node.tree_text == f"[] (0 strings)"
        assert node.column_text == "<empty>"
    elif len(data) == 1:
        assert node.tree_text == f"[{node.start} : {node.end}] ({node.end - node.start + 1} string)"
        assert node.column_text == f"{data[0]!r}"
    elif len(data) == 2:
        assert node.tree_text == f"[{node.start} : {node.end}] ({node.end - node.start + 1} strings)"
        assert node.column_text == ",".join(map(repr, data))
    else:
        assert node.tree_text == f"[{node.start} : {node.end}] ({node.end - node.start + 1} strings)"
        assert node.column_text == f"{data[node.start]!r} ... {data[node.end]!r}"


@given(st.lists(st.text()))
def test_split(data: List):
    node = Node(data)

    if len(data) < 2:
        with pytest.raises(AssertionError):
            node.split()
    else:
        children = node.split()

        if len(data) % 2 == 0:
            assert children[0].size == children[1].size == len(data) // 2
        else:
            assert children[0].size == len(data) // 2 + 1
            assert children[1].size == len(data) // 2

        assert sum(node.size for node in children) == len(data)
        assert reduce(operator.add, (list(node.items) for node in children), []) == data
