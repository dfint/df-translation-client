import pytest

from tkinter_helpers import Packer, set_parent, ParentSetter, Grid


@pytest.mark.parametrize("context_manager", [set_parent, ParentSetter, Grid, Packer])
def test_context_managers(context_manager, mocker):
    default_root_wrapper = mocker.Mock()
    mocker.patch("tkinter_helpers.default_root_wrapper", default_root_wrapper)

    old_default_root = mocker.Mock(name="old default_root")
    default_root_wrapper.default_root = old_default_root

    with pytest.raises(ValueError):
        with context_manager(mocker.Mock(name="parent")) as obj:
            assert (default_root_wrapper.default_root == obj  # case for set_parent
                    or default_root_wrapper.default_root == obj.parent)
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
