"""Headless Qt/PyQtGraph integration tests for Milestone 4 signal plotting."""

from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from cantracelab.gui import TraceViewer

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_LOG = ROOT / "samples" / "demo.log"
SAMPLE_DBC = ROOT / "samples" / "demo.dbc"


@pytest.fixture(scope="module")
def app():
    application = QApplication.instance() or QApplication([])
    yield application


def test_loads_default_speed_plots_with_separate_axes(app):
    viewer = TraceViewer()
    try:
        assert viewer.open_path(SAMPLE_LOG)
        assert viewer.plot_widgets == []
        assert viewer.open_dbc(SAMPLE_DBC)
        assert viewer.plot_selection.count() == 5
        assert len(viewer.plot_widgets) == 2
        selected = [
            viewer._signal_series[viewer.plot_selection.item(i).data(Qt.ItemDataRole.UserRole)]
            for i in range(viewer.plot_selection.count())
            if viewer.plot_selection.item(i).checkState() == Qt.CheckState.Checked
        ]
        assert {series.key.signal_name for series in selected} == {
            "VehicleSpeed", "EngineSpeed"
        }
        assert "2 signals" in viewer.plot_status.text()
    finally:
        viewer.close()


def test_multiple_units_plot_independently_and_ignore_frame_filters(app):
    viewer = TraceViewer()
    try:
        assert viewer.open_path(SAMPLE_LOG)
        assert viewer.open_dbc(SAMPLE_DBC)
        for i in range(viewer.plot_selection.count()):
            item = viewer.plot_selection.item(i)
            series = viewer._signal_series[item.data(Qt.ItemDataRole.UserRole)]
            item.setCheckState(
                Qt.CheckState.Checked
                if series.key.signal_name in {"VehicleSpeed", "CoolantTemperature", "EngineSpeed"}
                else Qt.CheckState.Unchecked
            )
        viewer.update_plots()
        assert len(viewer.plot_widgets) == 3
        series_before = tuple(viewer._signal_series)
        viewer.id_filter.setText("456")
        assert viewer.proxy.rowCount() == 1
        assert viewer._signal_series == series_before
        assert len(viewer.plot_widgets) == 3
    finally:
        viewer.close()


def test_clear_plots_preserves_trace_and_decoder(app):
    viewer = TraceViewer()
    try:
        assert viewer.open_path(SAMPLE_LOG)
        assert viewer.open_dbc(SAMPLE_DBC)
        viewer.clear_plots()
        assert viewer.plot_widgets == []
        assert viewer.model.rowCount() == 3
        assert viewer.decoder is not None
        assert "Check signals" in viewer.plot_status.text()
    finally:
        viewer.close()
