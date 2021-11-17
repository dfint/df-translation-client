import pytest

from tkinter_helpers import Packer, set_parent


def test_set_parent(mocker):
    default_root_wrapper = mocker.Mock()
    mocker.patch("tkinter_helpers.default_root_wrapper", default_root_wrapper)

    old_default_root = mocker.Mock(name="old default_root")
    default_root_wrapper.default_root = old_default_root

    with pytest.raises(ValueError):
        with set_parent(mocker.Mock(name="parent")) as parent:
            assert default_root_wrapper.default_root == parent
            raise ValueError

    assert default_root_wrapper.default_root == old_default_root


def test_packer(mocker):
    default_root_wrapper = mocker.Mock()
    mocker.patch("tkinter_helpers.default_root_wrapper", default_root_wrapper)

    old_default_root = mocker.Mock(name="old default_root")
    default_root_wrapper.default_root = old_default_root

    widget = mocker.Mock(name="widget")
    options = dict(side="left", expand=1, fill="X", padx=1)
    with pytest.raises(ValueError):
        with Packer(mocker.Mock(name="parent"), **options) as packer:
            assert default_root_wrapper.default_root == packer.parent
            packer.pack_all(widget)
            widget.pack.assert_called_with(**options)
            raise ValueError

    assert default_root_wrapper.default_root == old_default_root
