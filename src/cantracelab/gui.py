"""Desktop CAN Trace Viewer (Milestone 2).

Run with: python -m cantracelab.gui [optional trace filename]
"""

import argparse
import sys
from pathlib import Path

import can
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from .frame_model import FrameTableModel, TraceFilterProxyModel
from .trace import load_frames, summarize


class TraceViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CANTraceLab — CAN Trace Viewer")
        self.resize(1100, 700)
        self.current_file: Path | None = None

        container = QWidget()
        self.setCentralWidget(container)
        layout = QVBoxLayout(container)

        heading = QLabel("CANTraceLab")
        heading.setObjectName("heading")
        subtitle = QLabel("Offline CAN trace inspection · Milestone 2")
        subtitle.setObjectName("subtitle")
        layout.addWidget(heading)
        layout.addWidget(subtitle)

        toolbar = QHBoxLayout()
        open_button = QPushButton("Open CAN Log…")
        open_button.clicked.connect(self.choose_file)
        toolbar.addWidget(open_button)
        self.file_label = QLabel("No trace loaded")
        toolbar.addWidget(self.file_label, 1)
        layout.addLayout(toolbar)

        filters = QHBoxLayout()
        self.id_filter = QLineEdit()
        self.id_filter.setPlaceholderText("CAN ID contains (hex, e.g. 123)")
        self.channel_filter = QLineEdit()
        self.channel_filter.setPlaceholderText("Channel contains (e.g. vcan0)")
        self.payload_filter = QLineEdit()
        self.payload_filter.setPlaceholderText("Payload contains (hex bytes)")
        filters.addWidget(self.id_filter, 2)
        filters.addWidget(self.channel_filter, 2)
        filters.addWidget(self.payload_filter, 3)
        layout.addLayout(filters)

        self.model = FrameTableModel()
        self.proxy = TraceFilterProxyModel(self)
        self.proxy.setSourceModel(self.model)
        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.sortByColumn(0, Qt.SortOrder.AscendingOrder)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        for col in range(len(FrameTableModel.HEADERS)):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.table, 1)

        self.summary_label = QLabel("0 frames · 0 unique IDs · 0.0 s")
        layout.addWidget(self.summary_label)
        self.statusBar().showMessage("Open a .log, .asc or .blf file to begin")

        for field in (self.id_filter, self.channel_filter, self.payload_filter):
            field.textChanged.connect(self.apply_filters)

        open_action = QAction("Open CAN Log…", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.choose_file)
        self.menuBar().addMenu("File").addAction(open_action)

        self.setStyleSheet("""
        QMainWindow { background: #111827; color: #e5e7eb; }
        QWidget { color: #e5e7eb; font-size: 13px; }
        QLabel#heading { font-size: 23px; font-weight: bold; }
        QLabel#subtitle { color: #9ca3af; }
        QLineEdit, QTableView { background: #1f2937; color: #e5e7eb;
                                 border: 1px solid #374151; padding: 5px; }
        QPushButton { background: #2563eb; color: white; border-radius: 5px;
                      padding: 9px 13px; }
        QPushButton:hover { background: #1d4ed8; }
        QHeaderView::section { background: #374151; color: white; padding: 7px; }
        QTableView::item:selected { background: #1d4ed8; }
        QMenuBar, QMenu { background: #1f2937; }
        """)

    def choose_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open CAN trace", "", "CAN logs (*.log *.asc *.blf)"
        )
        if filename:
            self.open_path(filename)

    def open_path(self, filename: str | Path) -> bool:
        """Load a file, preserving the previous trace if parsing fails."""
        try:
            frames = load_frames(filename)
        except (OSError, ValueError, can.CanError) as exc:
            self.statusBar().showMessage(f"Unable to load trace: {exc}")
            QMessageBox.critical(self, "Unable to open CAN trace", str(exc))
            return False

        self.current_file = Path(filename)
        self.model.set_frames(frames)
        self.file_label.setText(self.current_file.name)
        self.file_label.setToolTip(str(self.current_file))
        self.apply_filters()
        self.statusBar().showMessage(f"Loaded {len(frames)} frames from {self.current_file.name}")
        return True

    def apply_filters(self):
        self.proxy.set_filters(
            can_id=self.id_filter.text(),
            channel=self.channel_filter.text(),
            payload=self.payload_filter.text(),
        )
        self.update_summary()

    def update_summary(self):
        frames = [self.model.frame_at(i) for i in range(self.model.rowCount())]
        stats = summarize(frames)
        self.summary_label.setText(
            f"Showing {self.proxy.rowCount():,} of {stats['frames']:,} frames · "
            f"{stats['unique_ids']} unique IDs · {stats['duration_s']:.6f} s duration"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Launch the CANTraceLab desktop viewer")
    parser.add_argument("file", nargs="?", help="Optional CAN log to open on startup")
    args = parser.parse_args(argv)
    app = QApplication.instance() or QApplication(sys.argv[:1])
    window = TraceViewer()
    if args.file:
        window.open_path(args.file)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
