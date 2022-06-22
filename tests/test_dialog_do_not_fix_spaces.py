import string

from df_translation_client.frames.dialog_do_not_fix_spaces import HighlightedSpacesItem, SPACE_PLACEHOLDER
from hypothesis import given, strategies as st


@given(
    st.text(alphabet=" "),
    st.text(alphabet=string.digits + string.ascii_letters + string.punctuation + " "),
    st.text(alphabet=" ")
)
def test_highlight_spaces(leading_spaces, text, trailing_spaces):
    text_with_spaces = leading_spaces + text.strip() + trailing_spaces
    expected_result = SPACE_PLACEHOLDER * len(leading_spaces) + text.strip() + SPACE_PLACEHOLDER * len(trailing_spaces)
    assert str(HighlightedSpacesItem(text_with_spaces)) == expected_result
