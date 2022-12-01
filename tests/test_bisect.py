from typing import List

import pytest
from hypothesis import given
from hypothesis import strategies as st

from df_translation_client.widgets.bisect_tool import Node


@given(st.lists(st.text()))
def test_node(data):
    node = Node(data)
    assert node.size == len(data)
    assert node.start == 0 and node.end == len(data) - 1
    if len(data) == 0:
        assert node.tree_text == "[] (0 strings)"
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
        child_1, child_2 = node.split()

        if len(data) % 2 == 0:
            assert child_1.size == child_2.size == len(data) // 2
        else:
            assert child_1.size == len(data) // 2 + 1
            assert child_2.size == len(data) // 2

        assert child_1.size + child_2.size == len(data)
        assert list(child_1.items) + list(child_2.items) == data
