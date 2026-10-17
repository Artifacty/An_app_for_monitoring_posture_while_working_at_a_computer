"""Страницы приложения: Мониторинг, Статистика, Последствия, Настройки.

Все данные на страницах — заглушки. Backend подключается через методы set_* и сигналы.
"""
from __future__ import annotations

from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtGui import QImage
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from gui.widgets import BarChart, Card, MetricRow, ScoreRing, StatusPill, VideoView


def _page_header(title: str, subtitle: str) -> tuple[QVBoxLayout, QLabel]:
    box = QVBoxLayout()
    box.setSpacing(2)
    h1 = QLabel(title)
    h1.setObjectName("h1")
    sub = QLabel(subtitle)
    sub.setObjectName("muted")
    box.addWidget(h1)
    box.addWidget(sub)
    return box, sub


class MonitorPage(QWidget):
    calibrate_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("page")
        self._running = False
        self._calibrated = False
        self._countdown = 0
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

        # --- шапка
        header = QHBoxLayout()
        titles, _ = _page_header("Мониторинг", "Камера анализирует вашу позу в реальном времени")
        header.addLayout(titles)
        header.addStretch()
        self.pill = StatusPill()
        header.addWidget(self.pill, alignment=Qt.AlignTop)

        # --- камера
        self.video = VideoView()

        # --- правая колонка
        self.score = ScoreRing()
        score_card = Card("Оценка осанки")
        score_card.body.addWidget(self.score, alignment=Qt.AlignHCenter)
        self.score_caption = QLabel("Нет данных")
        self.score_caption.setObjectName("muted")
        self.score_caption.setAlignment(Qt.AlignHCenter)
        score_card.body.addWidget(self.score_caption)

        metrics_card = Card("Показатели")
        self.m_shoulders = MetricRow("Наклон плеч")
        self.m_head = MetricRow("Наклон головы вперёд")
        self.m_distance = MetricRow("Расстояние до экрана")
        for m in (self.m_shoulders, self.m_head, self.m_distance):
            metrics_card.body.addWidget(m)

        calib_card = Card("Калибровка")
        self.calib_status = QLabel("Не выполнена")
        self.calib_status.setObjectName("muted")
        self.calib_hint = QLabel(
            "Сядьте так, как считаете правильным, и нажмите кнопку. "
            "Это ваша эталонная поза."
        )
        self.calib_hint.setObjectName("small")
        self.calib_hint.setWordWrap(True)
        self.btn_calibrate = QPushButton("Откалибровать позу")
        self.btn_calibrate.setObjectName("primary")
        self.btn_calibrate.setCursor(Qt.PointingHandCursor)
        self.btn_calibrate.clicked.connect(self._start_calibration)
        calib_card.body.addWidget(self.calib_status)
        calib_card.body.addWidget(self.calib_hint)
        calib_card.body.addWidget(self.btn_calibrate)

        side = QVBoxLayout()
        side.setSpacing(14)
        side.addWidget(score_card)
        side.addWidget(metrics_card)
        side.addWidget(calib_card)
        side.addStretch()
        side_w = QWidget()
        side_w.setLayout(side)
        side_w.setFixedWidth(300)

        body = QHBoxLayout()
        body.setSpacing(18)
        body.addWidget(self.video, stretch=1)
        body.addWidget(side_w)

        # --- нижняя строка
        self.fps = QLabel("FPS: —")
        self.fps.setObjectName("small")

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 18)
        root.setSpacing(16)
        root.addLayout(header)
        root.addLayout(body, stretch=1)
        root.addWidget(self.fps)

        self.set_running(False)

    # --- API для MainWindow / backend --------------------------------
    def show_frame(self, image: QImage, points: list) -> None:
        self.video.show_frame(image, points)

    def set_fps(self, fps: float | None) -> None:
        self.fps.setText("FPS: —" if fps is None else f"FPS: {fps:.0f}")

    def set_running(self, running: bool) -> None:
        self._running = running
        self.btn_calibrate.setEnabled(running)
        if not running:
            self._timer.stop()
            self.video.show_idle()
            self.video.set_overlay(None)
            self.score.set_value(None)
            self.score_caption.setText("Нет данных")
            for m in (self.m_shoulders, self.m_head, self.m_distance):
                m.set_value("—", None)
            self.set_fps(None)
        self._refresh_pill()

    def set_calibrated(self, done: bool) -> None:
        self._calibrated = done
        self.calib_status.setText("Выполнена ✓" if done else "Не выполнена")
        self.btn_calibrate.setText("Откалибровать заново" if done else "Откалибровать позу")
        self._refresh_pill()

    def _refresh_pill(self) -> None:
        if not self._running:
            self.pill.set_state("off", "Выключено")
        elif not self._calibrated:
            self.pill.set_state("warn", "Нужна калибровка")
        else:
            self.pill.set_state("ok", "Работает")

    # --- калибровка (демо-отсчёт; TODO backend) ----------------------
    def _start_calibration(self) -> None:
        self.calibrate_requested.emit()
        self._countdown = 3
        self.btn_calibrate.setEnabled(False)
        self.video.set_overlay(str(self._countdown))
        self._timer.start()

    def _tick(self) -> None:
        self._countdown -= 1
        if self._countdown > 0:
            self.video.set_overlay(str(self._countdown))
            return
        self._timer.stop()
        self.video.set_overlay(None)
        self.btn_calibrate.setEnabled(self._running)
        # TODO (backend): здесь результат калибровки приходит из engine.posture_logic
        self.set_calibrated(True)


class StatsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("page")

        titles, _ = _page_header("Статистика", "Как менялась ваша осанка за последние дни")

        # TODO (backend/data): заменить на данные из SQLite (процент «хорошей» осанки по дням)
        demo = [("Пн", 72), ("Вт", 64), ("Ср", 81), ("Чт", 55), ("Пт", 47), ("Сб", 88), ("Вс", 76)]
        chart_card = Card("Хорошая осанка по дням, %")
        chart_card.body.addWidget(BarChart(demo))
        note = QLabel("Пример данных — реальная статистика появится после подключения базы.")
        note.setObjectName("small")
        chart_card.body.addWidget(note)

        tiles = QHBoxLayout()
        tiles.setSpacing(14)
        for caption, value in (
            ("Среднее за неделю", "69%"),
            ("Дольше всего без перерыва", "2 ч 10 м"),
            ("Предупреждений сегодня", "12"),
        ):
            c = Card()
            v = QLabel(value)
            v.setObjectName("big")
            cap = QLabel(caption)
            cap.setObjectName("muted")
            c.body.addWidget(v)
            c.body.addWidget(cap)
            tiles.addWidget(c)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 18)
        root.setSpacing(16)
        root.addLayout(titles)
        root.addLayout(tiles)
        root.addWidget(chart_card, stretch=1)


class InfoPage(QWidget):
    """Последствия плохой осанки. Тексты — заготовки, их нужно заменить проверенными."""

    ITEMS = [
        ("Шея и плечи", "Наклон головы вперёд увеличивает нагрузку на мышцы шеи и верхней части спины."),
        ("Поясница", "Длительное сидение с округлённой спиной связано с болью в пояснице."),
        ("Головные боли", "Напряжение мышц шеи может сопровождаться головными болями."),
        ("Дыхание и энергия", "Сутулость ограничивает подвижность грудной клетки."),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("page")
        titles, _ = _page_header(
            "Последствия", "К чему может привести длительная неправильная осанка"
        )

        grid = QGridLayout()
        grid.setSpacing(14)
        for i, (title, text) in enumerate(self.ITEMS):
            card = Card(title)
            lbl = QLabel(text)
            lbl.setObjectName("muted")
            lbl.setWordWrap(True)
            card.body.addWidget(lbl)
            card.body.addStretch()
            grid.addWidget(card, i // 2, i % 2)

        disclaimer = QLabel(
            "Это профилактическая информация, а не диагноз. "
            "TODO: добавить источники и проверить формулировки."
        )
        disclaimer.setObjectName("small")
        disclaimer.setWordWrap(True)

        inner = QWidget()
        inner_lay = QVBoxLayout(inner)
        inner_lay.setContentsMargins(0, 0, 0, 0)
        inner_lay.addLayout(grid)
        inner_lay.addWidget(disclaimer)
        inner_lay.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(inner)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 18)
        root.setSpacing(16)
        root.addLayout(titles)
        root.addWidget(scroll, stretch=1)


class SettingsPage(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("page")
        titles, _ = _page_header("Настройки", "Предупреждения и работа камеры")

        alerts = Card("Предупреждения")
        self.sound = QCheckBox("Звуковой сигнал")
        self.sound.setChecked(True)
        self.popup = QCheckBox("Уведомление на экране")
        self.popup.setChecked(True)
        self.breaks = QCheckBox("Напоминать о перерыве каждые 45 минут")
        for c in (self.sound, self.popup, self.breaks):
            alerts.body.addWidget(c)

        sens = Card("Чувствительность")
        self.sens_label = QLabel("Средняя")
        self.sens_label.setObjectName("muted")
        self.sens = QSlider(Qt.Horizontal)
        self.sens.setRange(1, 3)
        self.sens.setValue(2)
        self.sens.valueChanged.connect(
            lambda v: self.sens_label.setText({1: "Низкая", 2: "Средняя", 3: "Высокая"}[v])
        )
        self.delay_label = QLabel("Предупреждать, если плохая поза длится: 15 с")
        self.delay_label.setObjectName("muted")
        self.delay = QSlider(Qt.Horizontal)
        self.delay.setRange(5, 60)
        self.delay.setValue(15)
        self.delay.valueChanged.connect(
            lambda v: self.delay_label.setText(f"Предупреждать, если плохая поза длится: {v} с")
        )
        sens.body.addWidget(self.sens_label)
        sens.body.addWidget(self.sens)
        sens.body.addWidget(self.delay_label)
        sens.body.addWidget(self.delay)

        cam = Card("Камера")
        self.camera = QComboBox()
        self.camera.addItems(["Камера 0 (по умолчанию)", "Камера 1"])
        cam.body.addWidget(self.camera)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 18)
        root.setSpacing(14)
        root.addLayout(titles)
        root.addWidget(alerts)
        root.addWidget(sens)
        root.addWidget(cam)
        root.addStretch()
