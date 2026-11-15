"""Qt UI regression tests for readability and safe proxy refresh behavior."""

import warnings
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from cantracelab.frame_model import FrameTableModel, TraceFilterProxyModel
from cantracelab.gui import TraceViewer
from cantracelab.trace import Frame

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def app():
    application = QApplication.instance() or QApplication([])
    yield application


def test_tabs_use_readable_dark_theme(app):
    viewer = TraceViewer()
    try:
        css = viewer.styleSheet()
        assert "QTabBar::tab" in css
        assert "QTabBar::tab:selected" in css
        assert "#e5e7eb" in css
        assert viewer.analysis_tabs.count() == 2
    finally:
        viewer.close()


def test_selected_frame_value_is_human_readable(app):
    viewer = TraceViewer()
    try:
        assert viewer.open_path(ROOT / "samples" / "demo.log")
        assert viewer.open_dbc(ROOT / "samples" / "demo.dbc")
        assert viewer.signal_table.item(0, 1).text() == "87.21"
        # Formatting is presentation-only; the underlying decoder retains
        # full precision, and signal plots continue using their raw values.
        assert viewer.decoder is not None
        frame = viewer.model.frame_at(0)
        decoded = viewer.decoder.decode(frame)
        assert float(decoded.signals[0].value) == pytest.approx(87.21)
    finally:
        viewer.close()


def test_proxy_refresh_filters_and_sorting_without_deprecation(app):
    frames = [
        Frame(10.0, "vcan0", 0x123, b"\x11", False, False, False),
        Frame(2.0, "can1", 0x456, b"\x22", False, False, False),
        Frame(3.0, "vcan0", 0x123, b"\x33", False, False, False),
    ]
    proxy = TraceFilterProxyModel()
    proxy.setSourceModel(FrameTableModel(frames))
    proxy.sort(0, Qt.SortOrder.AscendingOrder)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always", DeprecationWarning)
        proxy.set_filters(can_id="123")
        assert proxy.rowCount() == 2
        assert [float(proxy.data(proxy.index(i, 0))) for i in range(2)] == [3.0, 10.0]
        proxy.set_filters(channel="can1")
        assert proxy.rowCount() == 1
        assert proxy.data(proxy.index(0, 2)) == "0x456"
        proxy.set_filters()
        assert proxy.rowCount() == 3
    assert not [warning for warning in caught if issubclass(warning.category, DeprecationWarning)]
