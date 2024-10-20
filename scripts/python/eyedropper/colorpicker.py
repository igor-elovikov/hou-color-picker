import hou
from PySide2.QtCore import QPoint, Qt
from PySide2.QtGui import QColor, QCursor
from PySide2.QtWidgets import QApplication

from .colorinfo import ColorInformation
from .screensview import Screenshot, ScreenshotsWidget
from .settings import settings
from .utils import set_parm_color

SHARP_PRECISION = 0.01
TOLERANCE = 0.0001


class ScreenshotScene:
    def __init__(self, screenshot: Screenshot):
        self.color_info = ColorInformation()
        self.screenshot = screenshot
        self.screenshot.scene.addItem(self.color_info)

    def update(self, pos: QPoint, owner):
        local_pos = pos - self.screenshot.rect.topLeft()
        self.color_info.setPos(local_pos)

        if self.screenshot.rect.contains(pos):
            self.color_info.show()
        else:
            self.color_info.hide()

        image_pos = local_pos * self.screenshot.screen.devicePixelRatio()
        image = self.screenshot.image
        if image.rect().contains(image_pos):
            self.color_info.color = QColor(image.pixel(image_pos.x(), image_pos.y()))
            owner.color = self.color_info.color


class ColorPicker(ScreenshotsWidget):
    def __init__(self, parent, parm: hou.Parm):
        super().__init__(parent)
        for screenshot in self.screenshots:
            screenshot.view.setMouseTracking(True)
            screenshot.view.mouseReleaseEvent = self.close_picker
            screenshot.view.mouseMoveEvent = self.on_mouse_move
            screenshot.view.keyPressEvent = self.on_key_press
            screenshot.view.setCursor(Qt.BlankCursor)

        self.parm = parm
        self.scenes = [ScreenshotScene(s) for s in self.screenshots]
        self.color = QColor()

        for scene in self.scenes:
            scene.update(QCursor.pos(), self)

    def closeEvent(self, event):
        self.setParent(None)
        event.accept()

    def on_mouse_move(self, event):
        for scene in self.scenes:
            scene.update(event.globalPos(), self)

    def close_picker(self, event):
        modifiers = QApplication.keyboardModifiers()

        is_shift = modifiers & Qt.ShiftModifier
        is_control = modifiers & Qt.ControlModifier

        transform = settings.transform
        if is_shift:
            transform = settings.transform_with_shift
        if is_control:
            transform = settings.transform_with_control

        set_parm_color(self.parm, self.color, transform)

        self.close_all()
        self.close()

    def on_key_press(self, event):
        modifiers = event.modifiers()
        shift_or_control = modifiers & Qt.ShiftModifier or modifiers & Qt.ControlModifier
        if not shift_or_control:
            self.close_all()
            self.close()

        event.accept()


def show_color_picker(parm: hou.Parm) -> None:
    parm_tuple = parm.tuple()
    if parm_tuple is not None:
        ui = ColorPicker(hou.qt.mainWindow(), parm_tuple)
        ui.show()
