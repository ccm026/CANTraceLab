"""Qt model/proxy tests, runnable headlessly with QT_QPA_PLATFORM=offscreen."""

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from cantracelab.frame_model import FrameTableModel, TraceFilterProxyModel
from cantracelab.trace import Frame


@pytest.fixture(scope="module")
def app():
    application = QApplication.instance() or QApplication([])
    yield application


def sample_frames():
    return [
        Frame(10.0, "vcan0", 0x123, b"\xAA", False, False, False),
        Frame(2.0, "can1", 0x456, b"\xBB\xCC", False, False, False),
        Frame(3.0, "vcan0", 0x123, b"\xDD", False, False, True),
    ]


def test_model_formats_rows_and_headers(app):
    model = FrameTableModel(sample_frames())
    assert model.rowCount() == 3
    assert model.columnCount() == 7
    assert model.headerData(2, Qt.Orientation.Horizontal) == "CAN ID"
    assert model.data(model.index(0, 2)) == "0x123"
    assert model.data(model.index(1, 4)) == "2"
    assert model.data(model.index(2, 6)) == "Remote"


def test_model_replacement_clears_previous_rows(app):
    model = FrameTableModel(sample_frames())
    model.set_frames([])
    assert model.rowCount() == 0
    model.set_frames(sample_frames()[:1])
    assert model.rowCount() == 1


def test_filtering_by_multiple_fields(app):
    model = FrameTableModel(sample_frames())
    proxy = TraceFilterProxyModel()
    proxy.setSourceModel(model)
    proxy.set_filters(can_id="123", channel="vcan0", payload="AA")
    assert proxy.rowCount() == 1
    assert proxy.data(proxy.index(0, 5)) == "AA"
    proxy.set_filters(can_id="456")
    assert proxy.rowCount() == 1
    assert proxy.data(proxy.index(0, 2)) == "0x456"


def test_timestamps_sort_as_numbers_not_text(app):
    model = FrameTableModel(sample_frames())
    proxy = TraceFilterProxyModel()
    proxy.setSourceModel(model)
    proxy.sort(0, Qt.SortOrder.AscendingOrder)
    assert [float(proxy.data(proxy.index(i, 0))) for i in range(3)] == [2.0, 3.0, 10.0]
