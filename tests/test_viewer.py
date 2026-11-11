"""Smoke test the desktop viewer using an offscreen Qt application in CI."""

import pytest
from PySide6.QtWidgets import QApplication, QMessageBox

from cantracelab.gui import TraceViewer


@pytest.fixture(scope="module")
def app():
    application = QApplication.instance() or QApplication([])
    yield application


def test_load_and_filter_sample_trace(app, tmp_path):
    path = tmp_path / "trace.log"
    path.write_text(
        "(1700000000.000000) vcan0 123#AABB\n"
        "(1700000000.010000) can1 456#CCDD\n",
        encoding="utf-8",
    )
    viewer = TraceViewer()
    assert viewer.open_path(path) is True
    assert viewer.model.rowCount() == 2
    viewer.channel_filter.setText("vcan0")
    assert viewer.proxy.rowCount() == 1
    assert "1 of 2" in viewer.summary_label.text()
    viewer.close()


def test_missing_file_does_not_erase_current_trace(app, tmp_path, monkeypatch):
    path = tmp_path / "ok.log"
    path.write_text("(1700000000.000000) vcan0 123#AA\n", encoding="utf-8")
    monkeypatch.setattr(QMessageBox, "critical", lambda *args, **kwargs: None)
    viewer = TraceViewer()
    assert viewer.open_path(path)
    assert not viewer.open_path(tmp_path / "missing.log")
    assert viewer.model.rowCount() == 1
    assert viewer.current_file == path
    viewer.close()
