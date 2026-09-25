"""
orb_window.py — Opens the Friday orb as a desktop window using PyQt5.
Run this instead of opening orb.html manually in a browser.

Chrome-window-like behavior:
- A thin custom title bar sits ABOVE the QWebEngineView and handles dragging.
  (QWebEngineView is a real browser engine — it captures its own mouse
  events, so dragging by clicking on the orb graphic itself won't reach
  the window. The title bar strip is outside the webview, so it works
  reliably.)
- A real minimize button (frameless windows have none by default;
  showMinimized() has to be called explicitly).
- Close button, kept alongside the existing right-click-to-close.
"""

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QSizePolicy
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QIcon


TITLE_BAR_HEIGHT = 28


class TitleBar(QWidget):
    """Thin draggable strip with minimize/close buttons.

    Kept as its own widget (not baked into OrbWindow) so mouse events
    land on it directly instead of being intercepted by the webview.
    """

    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self._drag_pos = None

        self.setFixedHeight(TITLE_BAR_HEIGHT)
        self.setStyleSheet("background: rgba(0, 0, 0, 0.001);")  # invisible but still receives events
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 0, 6, 0)
        layout.setSpacing(6)
        layout.addStretch()  # push buttons to the right, like a normal window

        btn_style = """
            QPushButton {
                background: rgba(255, 255, 255, 0.08);
                border: none;
                border-radius: 10px;
                color: white;
                font-size: 12px;
                min-width: 20px;
                min-height: 20px;
                max-width: 20px;
                max-height: 20px;
            }
            QPushButton:hover { background: rgba(255, 255, 255, 0.25); }
        """
        close_style = btn_style + "QPushButton:hover { background: #e81123; }"

        self.minimize_btn = QPushButton("–")
        self.minimize_btn.setStyleSheet(btn_style)
        self.minimize_btn.clicked.connect(self.parent_window.showMinimized)

        self.close_btn = QPushButton("✕")
        self.close_btn.setStyleSheet(close_style)
        self.close_btn.clicked.connect(self.parent_window.close)

        layout.addWidget(self.minimize_btn)
        layout.addWidget(self.close_btn)

    # --- dragging lives here, not on OrbWindow, since this widget
    # actually receives the mouse events ---
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.parent_window.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self._drag_pos is not None:
            self.parent_window.move(event.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


class OrbWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Window settings
        self.setWindowTitle("Friday")
        self.setFixedSize(420, 528)  # +28 for title bar
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Central widget = title bar (drag + minimize + close) stacked on
        # top of the orb webview
        central = QWidget()
        central.setAttribute(Qt.WA_TranslucentBackground)
        outer_layout = QVBoxLayout(central)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        self.title_bar = TitleBar(self)
        outer_layout.addWidget(self.title_bar)

        # Load the orb HTML file
        self.browser = QWebEngineView()
        html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "orb.html")
        self.browser.setUrl(QUrl.fromLocalFile(html_path))
        self.browser.setStyleSheet("background: transparent;")
        self.browser.page().setBackgroundColor(Qt.transparent)
        outer_layout.addWidget(self.browser)

        self.setCentralWidget(central)

        # Position window — bottom right corner of screen
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.width() - 440, screen.height() - 548)

    # Right-click anywhere still closes it too (kept from original)
    def contextMenuEvent(self, event):
        self.close()


def launch_orb():
    app = QApplication(sys.argv)
    app.setApplicationName("Friday")
    window = OrbWindow()
    window.show()
    app.exec_()


if __name__ == "__main__":
    launch_orb()