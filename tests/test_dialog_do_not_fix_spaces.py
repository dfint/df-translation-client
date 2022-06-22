import pytest

from df_translation_client.frames.dialog_do_not_fix_spaces import HighlightedSpacesItem


@pytest.mark.parametrize("text, expected", [
    ["  test   ", "••test•••"],
    ["test", "test"],
    ["", ""],
])
def test_highlight_spaces(text, expected):
    assert str(HighlightedSpacesItem(text)) == expected
