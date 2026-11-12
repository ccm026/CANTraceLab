"""GUI integration tests for the selected-frame DBC panel (offscreen in CI)."""

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

from cantracelab.gui import TraceViewer

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_LOG = ROOT / "samples" / "demo.log"
SAMPLE_DBC = ROOT / "samples" / "demo.dbc"


@pytest.fixture(scope="module")
def app():
    application = QApplication.instance() or QApplication([])
    yield application


def test_dbc_decode_panel_follows_selected_frame(app):
    viewer = TraceViewer()
    try:
        assert viewer.open_path(SAMPLE_LOG)
        assert viewer.open_dbc(SAMPLE_DBC)
        assert viewer.signal_table.rowCount() == 3
        assert "SensorFrame" in viewer.decode_status.text()
        assert viewer.signal_table.item(0, 0).text() == "VehicleSpeed"
        assert viewer.signal_table.item(0, 2).text() == "km/h"

        # The second frame in chronological order is 0x456.
        viewer.table.selectRow(1)
        assert "PowertrainStatus" in viewer.decode_status.text()
        assert viewer.signal_table.item(0, 0).text() == "EngineSpeed"
    finally:
        viewer.close()


def test_bad_dbc_does_not_replace_existing_database(app, tmp_path, monkeypatch):
    monkeypatch.setattr(QMessageBox, "critical", lambda *_args, **_kwargs: None)
    viewer = TraceViewer()
    try:
        assert viewer.open_path(SAMPLE_LOG)
        assert viewer.open_dbc(SAMPLE_DBC)
        previous = viewer.decoder
        malformed = tmp_path / "invalid.dbc"
        malformed.write_text("invalid DBC", encoding="utf-8")
        assert not viewer.open_dbc(malformed)
        assert viewer.decoder is previous
        assert viewer.dbc_file == SAMPLE_DBC
        assert "SensorFrame" in viewer.decode_status.text()
    finally:
        viewer.close()


def test_filter_selection_does_not_change_source_trace(app):
    viewer = TraceViewer()
    try:
        assert viewer.open_path(SAMPLE_LOG)
        assert viewer.open_dbc(SAMPLE_DBC)
        viewer.id_filter.setText("456")
        assert viewer.model.rowCount() == 3
        assert viewer.proxy.rowCount() == 1
        viewer.table.selectRow(0)
        assert "PowertrainStatus" in viewer.decode_status.text()
        viewer.id_filter.clear()
        assert viewer.model.rowCount() == 3
        assert viewer.proxy.rowCount() == 3
    finally:
        viewer.close()


def test_unknown_frame_shows_explanation_not_stale_signals(app, tmp_path):
    log = tmp_path / "unknown.log"
    log.write_text("(1700000000.000000) vcan0 777#11223344\n", encoding="utf-8")
    viewer = TraceViewer()
    try:
        assert viewer.open_path(log)
        assert viewer.open_dbc(SAMPLE_DBC)
        assert viewer.signal_table.rowCount() == 0
        assert "UNKNOWN" in viewer.decode_status.text()
    finally:
        viewer.close()
