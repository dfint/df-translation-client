import pytest

from df_translation_client.tkinter_helpers import Packer, set_parent, ParentSetter, Grid, GridCell, Row


@pytest.mark.parametrize("context_manager", [set_parent, ParentSetter, Grid, Packer])
def test_context_managers(context_manager, mocker):
    default_root_wrapper = mocker.Mock()
    mocker.patch("df_translation_client.tkinter_helpers.default_root_wrapper", default_root_wrapper)

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
    mocker.patch("df_translation_client.tkinter_helpers.default_root_wrapper", default_root_wrapper)

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


def test_grid_cell(mocker):
    widget = mocker.Mock(name="widget")

    options = dict(column=1, row=2, rowspan=1, columnspan=1, sticky="nswe")
    cell = GridCell(widget, **options)
    cell.grid()
    widget.grid.assert_called_with(**options)

    cell.grid(sticky="ns")
    widget.grid.assert_called_with(**options)  # initial options override arguments of .grid()


def test_row(mocker):
    mocker.patch("tkinter.Label", mocker.Mock(name="Label"))

    row = Row(mocker.Mock(name="parent"), index=0, grid_options=dict(sticky="nswe", padx=5, pady=5))
    cells = row.add_cells(..., "Test", ...,
                          GridCell(mocker.Mock(name="Entry"), columnspan=3),
                          mocker.Mock(name="Button"))

    assert [(cell.column, cell.columnspan) for cell in cells] == [(1, 2), (3, 3), (6, 1)]
