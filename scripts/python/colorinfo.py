from PySide2.QtCore import QPoint, QRectF, Qt
from PySide2.QtGui import QBrush, QColor, QFont, QPen
from PySide2.QtWidgets import QGraphicsItem


class ColorInformation(QGraphicsItem):
    def __init__(self, parent=None):
        super(ColorInformation, self).__init__(parent)
        self.color = QColor(255, 255, 0)
        self.font = QFont("courier", 10)
        self.font.setBold(True)
        self.pos = QPoint()

    def boundingRect(self):
        return QRectF(-15, -15, 145, 145)

    def paint(self, painter, option, widget=None):
        painter.setBrush(QBrush(self.color))
        painter.setFont(self.font)

        black_pen = QPen(Qt.black, 3, Qt.SolidLine)
        painter.setPen(black_pen)

        painter.drawLine(-10, 0, 10, 0)
        painter.drawLine(0, -10, 0, 10)

        white_pen = QPen(Qt.white, 1, Qt.SolidLine)
        painter.setPen(white_pen)

        painter.drawLine(-10, 0, 10, 0)
        painter.drawLine(0, -10, 0, 10)

        white_pen = QPen(Qt.white, 3, Qt.SolidLine)
        painter.setPen(white_pen)
        painter.drawRoundedRect(12, 12, 30, 74, 5, 5)

        painter.setBrush(QColor(0, 0, 0, 55))
        painter.setPen(QPen(Qt.transparent))
        painter.drawRect(44, 12, 74, 74)

        painter.setPen(QPen(Qt.red))
        painter.drawText(50, 26, "R: " + str(self.color.red()))

        painter.setPen(QPen(Qt.green))
        painter.drawText(50, 52, "G: " + str(self.color.green()))

        painter.setPen(QPen(QColor(0, 181, 249)))
        painter.drawText(50, 80, "B: " + str(self.color.blue()))
