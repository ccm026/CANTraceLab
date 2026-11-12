"""Desktop CAN Trace Viewer with DBC signal plotting (Milestone 4).

Run with: python -m cantracelab.gui [optional trace filename] [--dbc file.dbc]
"""

import argparse
import sys
from pathlib import Path

import can
import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTableView,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .dbc import DbcDecoder
from .frame_model import FrameTableModel, TraceFilterProxyModel
from .plot_series import SignalKey, SignalSeries, extract_signal_series
from .trace import load_frames, summarize


class TraceViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CANTraceLab — CAN Trace Viewer")
        self.resize(1180, 950)
        self.current_file: Path | None = None
        self.dbc_file: Path | None = None
        self.decoder: DbcDecoder | None = None
        self._signal_series: tuple[SignalSeries, ...] = ()
        self.plot_widgets: list[pg.PlotWidget] = []

        container = QWidget()
        self.setCentralWidget(container)
        layout = QVBoxLayout(container)

        heading = QLabel("CANTraceLab")
        heading.setObjectName("heading")
        subtitle = QLabel("Offline CAN trace inspection · DBC signal plotting (Milestone 4)")
        subtitle.setObjectName("subtitle")
        layout.addWidget(heading)
        layout.addWidget(subtitle)

        toolbar = QHBoxLayout()
        open_button = QPushButton("Open CAN Log…")
        open_button.clicked.connect(self.choose_file)
        toolbar.addWidget(open_button)
        dbc_button = QPushButton("Load DBC…")
        dbc_button.clicked.connect(self.choose_dbc)
        toolbar.addWidget(dbc_button)
        self.dbc_label = QLabel("No DBC loaded")
        toolbar.addWidget(self.dbc_label)
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

        # Decoding is intentionally read-only: selecting a row never alters raw frames.
        details = QGroupBox("Decoded signals — selected CAN frame")
        details_layout = QVBoxLayout(details)
        self.decode_status = QLabel("Load a DBC and select a frame to decode it")
        details_layout.addWidget(self.decode_status)
        self.signal_table = QTableWidget(0, 3)
        self.signal_table.setHorizontalHeaderLabels(("Signal", "Value", "Unit"))
        self.signal_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.signal_table.verticalHeader().setVisible(False)
        self.signal_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.signal_table.setMaximumHeight(175)
        details_layout.addWidget(self.signal_table)
        layout.addWidget(details)

        # Each selected numeric signal gets a separate, unit-specific y-axis.
        # This deliberately avoids plotting km/h and rpm on a misleading shared axis.
        plot_group = QGroupBox("Signal trends — entire CAN trace")
        plot_group_layout = QVBoxLayout(plot_group)
        self.plot_status = QLabel("Load a CAN log and DBC to plot decoded signals")
        plot_group_layout.addWidget(self.plot_status)
        plot_controls = QHBoxLayout()
        self.plot_selection = QListWidget()
        self.plot_selection.setMaximumHeight(100)
        self.plot_selection.setToolTip("Check one or more numeric DBC signals to plot")
        plot_controls.addWidget(self.plot_selection, 1)
        plot_actions = QVBoxLayout()
        update_plot_button = QPushButton("Update plots")
        update_plot_button.clicked.connect(self.update_plots)
        plot_actions.addWidget(update_plot_button)
        clear_plot_button = QPushButton("Clear plots")
        clear_plot_button.clicked.connect(self.clear_plots)
        plot_actions.addWidget(clear_plot_button)
        plot_actions.addStretch()
        plot_controls.addLayout(plot_actions)
        plot_group_layout.addLayout(plot_controls)
        self.plot_scroll = QScrollArea()
        self.plot_scroll.setWidgetResizable(True)
        self.plot_scroll.setMinimumHeight(245)
        self.plots_container = QWidget()
        self.plots_layout = QVBoxLayout(self.plots_container)
        self.plot_scroll.setWidget(self.plots_container)
        plot_group_layout.addWidget(self.plot_scroll, 1)
        layout.addWidget(plot_group, 2)

        self.table.selectionModel().currentRowChanged.connect(
            lambda _current, _previous: self.update_decoded()
        )

        self.summary_label = QLabel("0 frames · 0 unique IDs · 0.0 s")
        layout.addWidget(self.summary_label)
        self.statusBar().showMessage("Open a .log, .asc or .blf file to begin")

        for field in (self.id_filter, self.channel_filter, self.payload_filter):
            field.textChanged.connect(self.apply_filters)

        open_action = QAction("Open CAN Log…", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.choose_file)
        file_menu = self.menuBar().addMenu("File")
        file_menu.addAction(open_action)
        dbc_action = QAction("Load DBC…", self)
        dbc_action.setShortcut("Ctrl+D")
        dbc_action.triggered.connect(self.choose_dbc)
        file_menu.addAction(dbc_action)

        self.setStyleSheet("""
        QMainWindow { background: #111827; color: #e5e7eb; }
        QWidget { color: #e5e7eb; font-size: 13px; }
        QLabel#heading { font-size: 23px; font-weight: bold; }
        QLabel#subtitle { color: #9ca3af; }
        QLineEdit, QListWidget, QTableView, QTableWidget { background: #1f2937; color: #e5e7eb;
                                 border: 1px solid #374151; padding: 5px; }
        QPushButton { background: #2563eb; color: white; border-radius: 5px;
                      padding: 9px 13px; }
        QPushButton:hover { background: #1d4ed8; }
        QHeaderView::section { background: #374151; color: white; padding: 7px; }
        QTableView::item:selected { background: #1d4ed8; }
        QMenuBar, QMenu { background: #1f2937; }
        QGroupBox { border: 1px solid #374151; margin-top: 8px; padding: 8px; }
        QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
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
        if self.proxy.rowCount():
            self.table.selectRow(0)
        else:
            self.table.clearSelection()
        self.update_decoded()
        self.rebuild_signal_list()
        self.statusBar().showMessage(f"Loaded {len(frames)} frames from {self.current_file.name}")
        return True

    def choose_dbc(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load CAN database", "", "CAN databases (*.dbc)"
        )
        if filename:
            self.open_dbc(filename)

    def open_dbc(self, filename: str | Path) -> bool:
        """Load an independent database; invalid files leave the last good DBC active."""
        try:
            candidate = DbcDecoder.from_file(filename)
        except (OSError, ValueError) as exc:
            self.statusBar().showMessage(f"Unable to load DBC: {exc}")
            QMessageBox.critical(self, "Unable to load DBC", str(exc))
            return False

        self.decoder = candidate
        self.dbc_file = Path(filename)
        self.dbc_label.setText(f"DBC: {self.dbc_file.name} ({candidate.message_count} IDs)")
        self.dbc_label.setToolTip(str(self.dbc_file))
        self.update_decoded()
        self.rebuild_signal_list()
        self.statusBar().showMessage(f"Loaded DBC: {self.dbc_file.name}")
        return True

    def update_decoded(self) -> None:
        """Decode the current proxy row without modifying the source CAN log."""
        self.signal_table.setRowCount(0)
        if self.decoder is None:
            self.decode_status.setText("Load a DBC file to decode the selected frame")
            return
        selected = self.table.currentIndex()
        if not selected.isValid():
            self.decode_status.setText("Select a CAN frame to see decoded signals")
            return

        source_index = self.proxy.mapToSource(selected)
        if not source_index.isValid():
            self.decode_status.setText("No matching CAN frame selected")
            return

        frame = self.model.frame_at(source_index.row())
        decoded = self.decoder.decode(frame)
        if decoded.status != "decoded":
            self.decode_status.setText(f"{decoded.status.upper()}: {decoded.detail}")
            return

        self.decode_status.setText(
            f"{decoded.message_name} · 0x{frame.arbitration_id:X} · "
            f"{len(decoded.signals)} decoded signals"
        )
        self.signal_table.setRowCount(len(decoded.signals))
        for row, signal in enumerate(decoded.signals):
            for col, value in enumerate((signal.name, str(signal.value), signal.unit)):
                self.signal_table.setItem(row, col, QTableWidgetItem(value))

    def rebuild_signal_list(self) -> None:
        """Refresh available numeric signals after a successful trace/DBC load."""
        old_selection = {
            self._signal_series[item.data(Qt.ItemDataRole.UserRole)].key
            for item in (self.plot_selection.item(i) for i in range(self.plot_selection.count()))
            if item.checkState() == Qt.CheckState.Checked
            and 0 <= item.data(Qt.ItemDataRole.UserRole) < len(self._signal_series)
        }
        if self.decoder is None or self.model.rowCount() == 0:
            self._signal_series = ()
        else:
            frames = [self.model.frame_at(i) for i in range(self.model.rowCount())]
            self._signal_series = extract_signal_series(frames, self.decoder)

        self.plot_selection.clear()
        valid_old = old_selection.intersection({series.key for series in self._signal_series})
        speed_choices = [
            index for index, series in enumerate(self._signal_series)
            if "speed" in series.key.signal_name.casefold()
        ]
        default_indices = set((speed_choices + list(range(len(self._signal_series))))[:2])
        for index, series in enumerate(self._signal_series):
            item = QListWidgetItem(f"{series.key.label} · {series.sample_count} samples")
            item.setData(Qt.ItemDataRole.UserRole, index)
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            checked = series.key in valid_old or (not valid_old and index in default_indices)
            item.setCheckState(Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked)
            self.plot_selection.addItem(item)
        self.update_plots()

    def clear_plots(self) -> None:
        for index in range(self.plot_selection.count()):
            self.plot_selection.item(index).setCheckState(Qt.CheckState.Unchecked)
        self.update_plots()

    def update_plots(self) -> None:
        """Render selected signals without changing the raw trace or its filters."""
        while self.plots_layout.count():
            item = self.plots_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
        self.plot_widgets.clear()

        selected = [
            self._signal_series[self.plot_selection.item(i).data(Qt.ItemDataRole.UserRole)]
            for i in range(self.plot_selection.count())
            if self.plot_selection.item(i).checkState() == Qt.CheckState.Checked
        ]
        if not selected:
            if self.decoder is None:
                message = "Load a DBC to enable plotting"
            elif not self._signal_series:
                message = "No valid numeric signals found in this trace and DBC"
            else:
                message = "Check signals above and click Update plots"
            self.plot_status.setText(message)
            return

        self.plot_status.setText(
            f"Plotting {len(selected)} signals from the full trace · "
            "drag to pan, scroll to zoom, click a marker to inspect a value"
        )
        colors = ("#36c2f0", "#f8b454", "#a78bfa", "#34d399", "#fb7185")
        for index, series in enumerate(selected):
            plot = pg.PlotWidget(background="#111827")
            plot.setMinimumHeight(225)
            plot.showGrid(x=True, y=True, alpha=0.22)
            plot.setLabel("bottom", "Time from trace start", units="s")
            plot.setLabel("left", series.key.signal_name, units=series.key.unit or None)
            plot.setTitle(f"{series.key.message_name} · {series.key.channel or 'no channel'} "
                          f"· CAN 0x{series.key.arbitration_id:X}")
            plot.addLegend()
            color = colors[index % len(colors)]
            curve = plot.plot(
                series.times_s,
                series.values,
                pen=pg.mkPen(color, width=2),
                symbol="o",
                symbolPen=pg.mkPen(color),
                symbolBrush=color,
                symbolSize=6,
                name=series.key.signal_name,
            )
            curve.sigPointsClicked.connect(
                lambda _curve, points, _ev=None, key=series.key:
                self._inspect_plot_point(key, points)
            )
            self.plots_layout.addWidget(plot)
            self.plot_widgets.append(plot)

    def _inspect_plot_point(self, key: SignalKey, points: list) -> None:
        if not points:
            return
        point = points[0].pos()
        unit = f" {key.unit}" if key.unit else ""
        self.statusBar().showMessage(
            f"{key.message_name}.{key.signal_name}: "
            f"{point.y():.6g}{unit} at +{point.x():.6f} s "
            f"({key.channel or 'no channel'})"
        )

    def apply_filters(self):
        self.proxy.set_filters(
            can_id=self.id_filter.text(),
            channel=self.channel_filter.text(),
            payload=self.payload_filter.text(),
        )
        self.update_summary()
        self.update_decoded()

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
    parser.add_argument("--dbc", help="Optional DBC file to decode selected frames")
    args = parser.parse_args(argv)
    app = QApplication.instance() or QApplication(sys.argv[:1])
    window = TraceViewer()
    if args.file:
        window.open_path(args.file)
    if args.dbc:
        window.open_dbc(args.dbc)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
