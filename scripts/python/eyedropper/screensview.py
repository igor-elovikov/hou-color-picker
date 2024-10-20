from dataclasses import dataclass

from PySide2.QtCore import QObject, QRect, Qt
from PySide2.QtGui import QPixmap, QScreen
from PySide2.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QWidget


@dataclass
class ScreenshotData:
    pixmap: QPixmap
    rect: QRect
    screen: QScreen


class Screenshot(QObject):
    def __init__(self, screenshot: ScreenshotData, parent: QWidget):
        super().__init__(parent)
        self.rect = screenshot.rect
        self.screen = screenshot.screen
        self.pixmap = screenshot.pixmap
        self.image = self.pixmap.toImage()
        self.view = QGraphicsView(parent)
        self.scene = QGraphicsScene(parent)
        self.view.setGeometry(self.rect)
        self.scene.addPixmap(self.pixmap)
        self.view.setScene(self.scene)

        self.view.setWindowFlags(Qt.FramelessWindowHint)
        self.view.setWindowFlags(Qt.WindowType_Mask)
        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def show(self):
        self.view.showFullScreen()


class ScreenshotsWidget(QWidget):
    def __init__(self, parent):
        super().__init__(parent)

        self.screen_datas = [
            ScreenshotData(s.grabWindow(0), s.geometry(), s) for s in QApplication.screens()
        ]

        self.screenshots = [Screenshot(s, parent) for s in self.screen_datas]

        for screen in self.screenshots:
            screen.show()

    def close_all(self):
        for screen in self.screenshots:
            screen.view.close()
