"""Поток камеры. Только GUI-часть: захват кадров и передача в интерфейс.

Точка подключения backend'а: метод `_detect_landmarks(frame)`.
Сейчас он возвращает ЗАГЛУШКУ (статичные точки), чтобы было видно, как выглядит оверлей.
Друг заменяет её вызовом engine.pose_detector и возвращает список (x, y)
в нормализованных координатах 0..1 (как отдаёт MediaPipe).
"""
from __future__ import annotations

import time

import cv2
from PySide6.QtCore import QThread, Signal
from PySide6.QtGui import QImage


class CameraWorker(QThread):
    frame_ready = Signal(QImage, list)   # кадр, список нормализованных точек [(x, y), ...]
    fps_updated = Signal(float)
    error = Signal(str)

    def __init__(self, camera_index: int = 0, parent=None):
        super().__init__(parent)
        self._camera_index = camera_index
        self._running = False

    # --- управление ---------------------------------------------------
    def stop(self) -> None:
        self._running = False
        self.wait(3000)

    # --- основной цикл ------------------------------------------------
    def run(self) -> None:
        cap = cv2.VideoCapture(self._camera_index)
        if not cap.isOpened():
            self.error.emit("Не удалось открыть камеру. Проверьте подключение и права доступа.")
            return

        self._running = True
        frames, t0 = 0, time.monotonic()

        while self._running:
            ok, frame = cap.read()
            if not ok:
                self.error.emit("Камера перестала отдавать кадры.")
                break

            frame = cv2.flip(frame, 1)  # зеркало, как в видеозвонках
            points = self._detect_landmarks(frame)

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb.shape
            image = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888).copy()
            self.frame_ready.emit(image, points)

            frames += 1
            now = time.monotonic()
            if now - t0 >= 1.0:
                self.fps_updated.emit(frames / (now - t0))
                frames, t0 = 0, now

        cap.release()

    # --- ЗАГЛУШКА для backend'а --------------------------------------
    def _detect_landmarks(self, frame) -> list[tuple[float, float]]:
        """TODO (backend): заменить на engine.pose_detector.

        Возвращает демонстрационные точки: нос, уши, плечи.
        """
        return [
            (0.50, 0.30),  # нос
            (0.45, 0.29),  # левое ухо
            (0.55, 0.29),  # правое ухо
            (0.38, 0.55),  # левое плечо
            (0.62, 0.55),  # правое плечо
        ]
