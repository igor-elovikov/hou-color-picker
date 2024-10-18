class ScreenshotView(QGraphicsView):
    def __init__(self, parent, screen, parm, gradient_edit, ramp_sketch, hot_spot=QPoint(0, 0)):
        super(ScreenshotView, self).__init__(parent)

        self.setMouseTracking(True)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameStyle(QFrame.NoFrame)
        self.setGeometry(screen.geometry())

        self.hot_spot = hot_spot
        self.ramp_sketch = ramp_sketch
        self.gradient_edit = gradient_edit
        self.is_macos = sys.platform == "darwin"

        self.screenshot_scene = QGraphicsScene(parent)
        self.setScene(self.screenshot_scene)

        self.parm = parm  # type: hou.Parm
        self.parent_screen: QScreen = screen

        self.draw_path = False

        self.initialize_scene()

        self.colors = []  # type: list[QColor]
        self.positions = []  # type: list[QPoint]
        self.picked_color = QColor()

        self.disable_gamma_correction = False
        self.transform_setting = eyedropperprefs.settings.transform

    def initialize_scene(self):
        self.path = QPainterPath()
        self.path_item = QGraphicsPathItem()
        self.color_info = ColorInformation()

        if not self.ramp_sketch:
            self.path_item.setPen(QPen(QColor(0, 200, 100, 200), 2))
        else:
            self.path_item.setPen(QPen(QColor(200, 200, 50, 255), 4))

        geometry = self.parent_screen.geometry()

        if sys.platform == "darwin":
            self.screen_pixmap = parent_screen.grabWindow(
                0, geometry.x(), geometry.y(), geometry.width(), geometry.height()
            )
        else:
            self.screen_pixmap = self.parent_screen.grabWindow(0)

        self.screen_image = self.screen_pixmap.toImage()  # type: QImage

        self.setSceneRect(0, 0, self.screen_pixmap.width(), self.screen_pixmap.height())

        self.screenshot_scene.addPixmap(self.screen_pixmap)
        self.screenshot_scene.addItem(self.path_item)
        self.screenshot_scene.addItem(self.color_info)

        # TODO: ???
        if self.is_macos:
            self.color_info.show()

        if self.ramp_sketch:
            self.color_info.hide()

        self.update_info_visibility()

    def clear_scene(self):
        self.screenshot_scene.clear()

    def update_info_visibility(self):
        if self.underMouse():
            self.color_info.show()
        else:
            self.color_info.hide()

    def update_info(self, pos):
        image_pos = pos * self.parent_screen.devicePixelRatio()
        if self.screen_image.rect().contains(image_pos):
            self.color_info.color = QColor(self.screen_image.pixel(image_pos.x(), image_pos.y()))
        self.color_info.setPos(pos)
        self.color_info.pos = pos

    def write_color_ramp(self):
        if len(self.colors) < 2:
            return

        color_points = []

        vlast_color = hou.Vector3(hou.qt.fromQColor(self.colors[0])[0].rgb())
        last_color_index = 0

        color_points.append((vlast_color, 0))

        # remove same keys in a row
        for index, color in enumerate(self.colors[1:]):
            color_index = index + 1
            vcolor = hou.Vector3(hou.qt.fromQColor(color)[0].rgb())
            dist = vcolor.distanceTo(vlast_color)

            if dist > TOLERANCE:
                # if color_index - last_color_index > 1 and dist > SHARP_PRECISION:
                #     color_points.append((hou.Vector3(vlast_color), color_index - 1))
                color_points.append((hou.Vector3(vcolor), color_index))
                vlast_color = vcolor
                last_color_index = color_index

        if color_points[-1][1] < (len(self.colors) - 1):
            color_points.append(
                (hou.Vector3(hou.qt.fromQColor(self.colors[-1])[0].rgb()), len(self.colors) - 1)
            )

        # Create a polyline representing ramp and remove inline points with Facet SOP
        points = [color_point[0] for color_point in color_points]
        pos = [color_point[1] for color_point in color_points]

        ramp_geo = hou.Geometry()

        pos_attrib = ramp_geo.addAttrib(
            hou.attribType.Point, "ramp_pos", 0.0, create_local_variable=False
        )

        ramp_points = ramp_geo.createPoints(points)
        fnum_points = float(len(self.colors) - 1)

        for ptnum, point in enumerate(ramp_points):
            point.setAttribValue(pos_attrib, float(pos[ptnum]) / fnum_points)

        ramp_poly = ramp_geo.createPolygons((ramp_points,), False)[0]  # type: hou.Face

        facet_verb = hou.sopNodeTypeCategory().nodeVerb("facet")  # type: hou.SopVerb

        facet_verb.setParms({"inline": 1, "inlinedist": 0.02})

        facet_verb.execute(ramp_geo, [ramp_geo])

        ramp_poly = ramp_geo.prim(0)
        ramp_points = ramp_poly.points()

        linear = hou.rampBasis.Linear

        basis = []
        keys = []
        values = []

        pos_attrib = ramp_geo.findPointAttrib("ramp_pos")

        for point in ramp_points:
            basis.append(linear)
            keys.append(point.attribValue(pos_attrib))
            values.append(tuple(point.position()))

        values = [transform_color(v, self.transform_setting) for v in values]

        ramp = hou.Ramp(basis, keys, values)
        self.parm.set(ramp)
        self.parm.pressButton()

    def mouseMoveEvent(self, event):
        pos = event.pos()  # * self.screen.devicePixelRatio()
        self.update_info(pos)

        # TODO: ???
        if self.is_macos and not self.ramp_sketch:
            self.color_info.show()

        if self.draw_path:
            path = self.path_item.path()
            path.lineTo(pos + self.hot_spot)
            self.path_item.setPath(path)
            self.colors.append(self.color_info.color)
            self.positions.append(pos)

        self.update_info_visibility()

        return QGraphicsView.mouseMoveEvent(self, event)

    def mousePressEvent(self, event):
        modifiers = QApplication.keyboardModifiers()

        if modifiers & Qt.ShiftModifier:
            self.disable_gamma_correction = True
            self.transform_setting = eyedropperprefs.settings.transform_with_shift

        if modifiers & Qt.ControlModifier:
            self.transform_setting = eyedropperprefs.settings.transform_with_control

        if self.gradient_edit or self.ramp_sketch:
            self.draw_path = True
            self.path.moveTo(event.pos() + self.hot_spot)
            self.path_item.setPath(self.path)
        else:
            self.picked_color = self.color_info.color

    def mouseReleaseEvent(self, event):
        if self.gradient_edit and self.draw_path:
            self.write_color_ramp()
        elif not self.gradient_edit:

            picked_color = hou.qt.fromQColor(self.picked_color)[0]
            out_color = transform_color(picked_color, self.transform_setting)

            if isinstance(self.parm, hou.ParmTuple) and len(self.parm) == 4:
                alpha = self.parm[3].eval()
                out_color = np.append(out_color, alpha)

            self.parm.set(out_color)

        hide_picker()


class ScreensMain(QMainWindow):
    def __init__(self, parm, gradient_edit, ramp_sketch, parent=None, screen=None):
        super(ScreensMain, self).__init__(parent)

        app = QApplication.instance()  # type: QApplication
        screens = app.screens()
        cursor_pos = QCursor.pos()

        self.setCursor(Qt.BlankCursor)

        screen_to_attach = screens[0] if screen is None else screen

        view = ScreenshotView(None, screen_to_attach, parm, gradient_edit, ramp_sketch)
        self.view = view
        self.setWindowFlag(Qt.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.FramelessWindowHint)
        self.setCentralWidget(view)
        self.setGeometry(screen_to_attach.geometry())
        self.show()

        view.update_info(cursor_pos)

        self.setMouseTracking(True)
        self.additional_windows: list[ScreensMain] = []

        if screen_to_attach.geometry().contains(cursor_pos) and not ramp_sketch:
            view.color_info.show()
        else:
            view.color_info.hide()

        if screen is None:
            for screen in screens[1:]:
                additional_window = ScreensMain(parm, gradient_edit, ramp_sketch, None, screen)
                self.additional_windows.append(additional_window)

    def hide_all(self):
        self.view.clear_scene()
        self.hide()

        if self.additional_windows:
            for window in self.additional_windows:
                window.view.clear_scene()
                window.hide()

    def show_all(self):
        self.show()
        for child in self.additional_windows:
            child.show()

    def keyPressEvent(self, event):
        modifiers = event.modifiers()
        shift_or_control = modifiers & Qt.ShiftModifier or modifiers & Qt.ControlModifier
        if not shift_or_control:
            hide_picker()

    def initialize(self):
        self.view.initialize_scene()
        self.view.update_info(QCursor.pos())
        for child in self.additional_windows:
            child.view.initialize_scene()
            child.view.update_info(QCursor.pos())
