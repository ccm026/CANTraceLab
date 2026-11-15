"""Headless Qt integration tests for timing diagnostics tab."""

from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

from cantracelab.gui import TraceViewer

ROOT = Path(__file__).resolve().parents[1]
SAMPLE = ROOT / "samples" / "timing_demo.log"
DBC = ROOT / "samples" / "demo.dbc"


@pytest.fixture(scope="module")
def app():
    application = QApplication.instance() or QApplication([])
    yield application


def test_timing_panel_populates_without_dbc_or_hardware(app):
    viewer = TraceViewer()
    try:
        assert viewer.open_path(SAMPLE)
        assert viewer.timing_key_combo.count() == 2
        assert "0x123" in viewer.timing_key_combo.currentText()
        assert viewer.timing_table.rowCount() == 4
        assert "No cycle threshold set" in viewer.timing_status.text()
    finally:
        viewer.close()


def test_expected_cycle_finds_one_possible_missing_message(app):
    viewer = TraceViewer()
    try:
        assert viewer.open_path(SAMPLE)
        viewer.timing_check.setChecked(True)
        viewer.timing_period.setValue(10.0)
        assert "1 possibly missing" in viewer.timing_status.text()
        assert "1 alerts" in viewer.timing_status.text()
        assert viewer.timing_table.item(2, 4).text() == "possible missing"
        assert viewer.timing_table.item(2, 5).text() == "1"
    finally:
        viewer.close()


def test_selecting_another_can_id_changes_report(app):
    viewer = TraceViewer()
    try:
        assert viewer.open_path(SAMPLE)
        viewer.timing_check.setChecked(True)
        viewer.timing_key_combo.setCurrentIndex(1)
        assert "0x456" in viewer.timing_status.text()
        assert viewer.timing_table.rowCount() == 3
        assert "0 possibly missing" in viewer.timing_status.text()
    finally:
        viewer.close()


def test_raw_frame_filters_do_not_modify_timing_analysis(app):
    viewer = TraceViewer()
    try:
        assert viewer.open_path(SAMPLE)
        viewer.timing_check.setChecked(True)
        before = viewer.timing_status.text()
        viewer.id_filter.setText("456")
        assert viewer.proxy.rowCount() == 4
        assert viewer.timing_status.text() == before
        assert viewer.timing_table.rowCount() == 4
    finally:
        viewer.close()


def test_dbc_plots_and_timing_can_coexist(app):
    viewer = TraceViewer()
    try:
        assert viewer.open_path(SAMPLE)
        assert viewer.open_dbc(DBC)
        assert len(viewer.plot_widgets) == 2
        assert viewer.timing_table.rowCount() == 4
        assert viewer.analysis_tabs.count() == 2
    finally:
        viewer.close()


def test_loading_invalid_file_preserves_previous_report(app, tmp_path, monkeypatch):
    monkeypatch.setattr(QMessageBox, "critical", lambda *args, **kwargs: None)
    viewer = TraceViewer()
    try:
        assert viewer.open_path(SAMPLE)
        old_status = viewer.timing_status.text()
        assert not viewer.open_path(tmp_path / "not-found.log")
        assert viewer.timing_status.text() == old_status
        assert viewer.timing_key_combo.count() == 2
    finally:
        viewer.close()


def test_empty_and_single_frame_traces_do_not_crash(app, tmp_path):
    single = tmp_path / "one.log"
    single.write_text("(1700000000.000000) vcan0 123#11223344\n", encoding="utf-8")
    viewer = TraceViewer()
    try:
        assert viewer.open_path(single)
        assert viewer.timing_table.rowCount() == 0
        assert "at least two frames" in viewer.timing_status.text()
    finally:
        viewer.close()
