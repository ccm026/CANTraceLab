"""Qt table model and sortable/filterable proxy for offline CAN frames."""

from collections.abc import Sequence

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QSortFilterProxyModel, Qt

from .filtering import frame_matches
from .trace import Frame

SORT_ROLE = Qt.ItemDataRole.UserRole + 1


class FrameTableModel(QAbstractTableModel):
    HEADERS = ("Timestamp (s)", "Channel", "CAN ID", "Format", "DLC", "Data (hex)", "Type")

    def __init__(self, frames: Sequence[Frame] = (), parent=None):
        super().__init__(parent)
        self._frames = list(frames)

    def set_frames(self, frames: Sequence[Frame]) -> None:
        self.beginResetModel()
        self._frames = list(frames)
        self.endResetModel()

    def frame_at(self, row: int) -> Frame:
        return self._frames[row]

    def rowCount(self, parent=QModelIndex()):   # noqa: B008
        return 0 if parent.isValid() else len(self._frames)

    def columnCount(self, parent=QModelIndex()):     # noqa: B008
        return 0 if parent.isValid() else len(self.HEADERS)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
            and 0 <= section < len(self.HEADERS)
        ):
            return self.HEADERS[section]
        return None

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._frames)):
            return None
        frame = self._frames[index.row()]
        values = (
            frame.timestamp,
            frame.channel,
            frame.arbitration_id,
            "Extended" if frame.is_extended_id else "Standard",
            len(frame.data),
            frame.data.hex(" ").upper(),
            "Error" if frame.is_error_frame else "Remote" if frame.is_remote_frame else "Data",
        )
        if role == Qt.ItemDataRole.DisplayRole:
            if index.column() == 0:
                return f"{frame.timestamp:.6f}"
            if index.column() == 2:
                return f"0x{frame.arbitration_id:X}"
            return str(values[index.column()])
        if role == SORT_ROLE:
            return values[index.column()]
        if role == Qt.ItemDataRole.TextAlignmentRole and index.column() in (0, 2, 4):
            return Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        return None


class TraceFilterProxyModel(QSortFilterProxyModel):
    """Filter frames without mutating the underlying log or its original ordering."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._id_text = ""
        self._channel_text = ""
        self._payload_text = ""
        self.setSortRole(SORT_ROLE)
        self.setDynamicSortFilter(True)

    def set_filters(self, *, can_id="", channel="", payload="") -> None:
        self._id_text = can_id
        self._channel_text = channel
        self._payload_text = payload
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        source = self.sourceModel()
        if not isinstance(source, FrameTableModel):
            return False
        return frame_matches(
            source.frame_at(source_row),
            can_id=self._id_text,
            channel=self._channel_text,
            payload=self._payload_text,
        )
