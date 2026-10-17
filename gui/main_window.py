"""Главное окно Posture Guard: боковая навигация + страницы."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from gui.pages import InfoPage, MonitorPage, SettingsPage, StatsPage
from gui.theme import build_stylesheet
from gui.widgets import ToggleSwitch
from gui.worker import CameraWorker


class MainWindow(QMainWindow):
    NAV = ["Мониторинг", "Статистика", "Последствия", "Настройки"]

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Posture Guard")
        self.resize(1180, 760)
        self.setMinimumSize(980, 640)
        self.setStyleSheet(build_stylesheet())

        self._worker: CameraWorker | None = None

        # --- страницы
        self.monitor = MonitorPage()
        self.stack = QStackedWidget()
        for page in (self.monitor, StatsPage(), InfoPage(), SettingsPage()):
            self.stack.addWidget(page)

        # --- боковая панель
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(0, 24, 0, 20)
        side.setSpacing(2)

        logo = QLabel("Posture Guard")
        logo.setObjectName("logo")
        logo.setContentsMargins(22, 0, 0, 18)
        side.addWidget(logo)

        group = QButtonGroup(self)
        group.setExclusive(True)
        for i, name in enumerate(self.NAV):
            btn = QPushButton(name)
            btn.setProperty("nav", True)
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setChecked(i == 0)
            group.addButton(btn, i)
            side.addWidget(btn)
        group.idClicked.connect(self.stack.setCurrentIndex)

        side.addStretch()

        # переключатель вкл/выкл
        power_row = QHBoxLayout()
        power_row.setContentsMargins(22, 0, 22, 0)
        self.power_label = QLabel("Защита осанки")
        self.power = ToggleSwitch()
        self.power.toggled.connect(self._on_power)
        power_row.addWidget(self.power_label)
        power_row.addStretch()
        power_row.addWidget(self.power)
        side.addLayout(power_row)

        # --- корень
        root = QWidget()
        root.setObjectName("root")
        lay = QHBoxLayout(root)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(sidebar)
        lay.addWidget(self.stack, stretch=1)
        self.setCentralWidget(root)

        self.monitor.calibrate_requested.connect(self._on_calibrate)

    # --- включение / выключение ---------------------------------------
    def _on_power(self, on: bool) -> None:
        self._start() if on else self._stop()

    def _start(self) -> None:
        self._worker = CameraWorker()
        self._worker.frame_ready.connect(self.monitor.show_frame)
        self._worker.fps_updated.connect(self.monitor.set_fps)
        self._worker.error.connect(self._on_error)
        self._worker.start()
        self.monitor.set_running(True)

    def _stop(self) -> None:
        if self._worker is not None:
            self._worker.stop()
            self._worker = None
        self.monitor.set_running(False)

    # --- калибровка ----------------------------------------------------
    def _on_calibrate(self) -> None:
        # TODO (backend): запустить калибровку через engine.posture_logic
        pass

    def _on_error(self, message: str) -> None:
        self.power.set_checked_silent(False)
        self._stop()
        QMessageBox.warning(self, "Ошибка камеры", message)

    def closeEvent(self, event) -> None:
        self._stop()
        super().closeEvent(event)
