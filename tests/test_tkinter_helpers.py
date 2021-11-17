from tkinter_helpers import Packer, set_parent


def test_set_parent(mocker):
    set_default_root = mocker.Mock()
    mocker.patch("tkinter_helpers.set_default_root", set_default_root)

    get_default_root = mocker.Mock()
    get_default_root.return_value = mocker.Mock(name="old default_root")
    mocker.patch("tkinter_helpers.get_default_root", get_default_root)

    with set_parent(mocker.Mock(name="parent")) as parent:
        set_default_root.assert_called_with(parent)

    set_default_root.assert_called_with(get_default_root.return_value)


def test_packer(mocker):
    set_default_root = mocker.Mock()
    mocker.patch("tkinter_helpers.set_default_root", set_default_root)

    get_default_root = mocker.Mock()
    get_default_root.return_value = mocker.Mock(name="old default_root")
    mocker.patch("tkinter_helpers.get_default_root", get_default_root)

    widget = mocker.Mock(name="widget")
    options = dict(side="left", expand=1, fill="X", padx=1)
    with Packer(mocker.Mock(name="parent"), **options) as packer:
        set_default_root.assert_called_with(packer.parent)
        packer.pack_all(widget)
        widget.pack.assert_called_with(**options)

    set_default_root.assert_called_with(get_default_root.return_value)
