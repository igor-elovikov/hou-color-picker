from dataclasses import dataclass, field, fields, is_dataclass
from enum import Enum
from typing import Any

import hou
from PySide2.QtWidgets import QComboBox, QHBoxLayout, QLabel, QMainWindow, QVBoxLayout, QWidget


def _strip_unused_keys(data_class: type, d: dict[str, Any]) -> dict[str, Any]:
    field_names = [f.name for f in fields(data_class)]
    return {key: d[key] for key in d if key in field_names}


def _from_dict(data_class: type, d: dict[str, Any] | Any) -> Any:
    print(data_class, d)
    if is_dataclass(data_class):
        field_types = {f.name: f.type for f in fields(data_class)}
        stripped_dict = _strip_unused_keys(data_class, d)
        return data_class(**{f: _from_dict(field_types[f], d[f]) for f in stripped_dict})
    return d


class NonOcioTransform(Enum):
    NO = "No Transform"
    GAMMA = "Gamma Correction"
    INVERSE_GAMMA = "Inverse Gamma Correction"


@dataclass
class TransformSettings:
    use_ocio: bool = True
    non_ocio_transform: NonOcioTransform = NonOcioTransform.GAMMA
    source_space: str = "sRGB - Texture"
    dest_space: str = "Linear Rec.709 (sRGB)"

    def set_source_space(self, space: str):
        self.source_space = space

    def set_dest_space(self, space: str):
        self.dest_space = space


@dataclass
class Settings:
    transform: TransformSettings = field(default_factory=TransformSettings)
    transform_with_shift: TransformSettings = field(
        default_factory=lambda: TransformSettings(dest_space="ACEScg")
    )
    transform_with_control: TransformSettings = field(
        default_factory=lambda: TransformSettings(dest_space="Raw")
    )


settings = Settings()


class OcioSpaceSelector(QComboBox):
    def __init__(self, initial: str, parent=None):
        super().__init__(parent)
        self.addItems(hou.Color.ocio_spaces())
        self.setCurrentText(initial)


class TransformSettingsEditor(QWidget):
    def __init__(self, target: TransformSettings, name: str, parent=None):
        super().__init__(parent)

        layout = QHBoxLayout()
        self.setLayout(layout)

        label = QLabel(name)
        label.setFixedWidth(400)
        layout.addWidget(label)

        source_space_selector = OcioSpaceSelector(target.source_space)
        source_space_selector.currentTextChanged.connect(lambda t: target.set_source_space(t))

        dest_space_selector = OcioSpaceSelector(target.dest_space)
        dest_space_selector.currentTextChanged.connect(lambda t: target.set_dest_space(t))

        layout.addWidget(source_space_selector)

        forward_arrow = QLabel()
        icon = hou.qt.Icon("BUTTONS_forward")
        forward_arrow.setPixmap(icon.pixmap(64, 64))
        layout.addWidget(forward_arrow)
        layout.addWidget(dest_space_selector)


settings_editor: Any = None


class SettingsEditor(QMainWindow):
    def __init__(self, parent=None):
        parent = parent or hou.qt.mainWindow()
        super().__init__(parent)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        layout.addWidget(TransformSettingsEditor(settings.transform, "Standart Transform: "))
        layout.addWidget(
            TransformSettingsEditor(settings.transform_with_shift, "Transform with [Shift]: ")
        )
        layout.addWidget(
            TransformSettingsEditor(settings.transform_with_control, "Transform with [Control]: ")
        )

    def closeEvent(self, event):
        global settings_editor
        settings_editor = None
        print(settings)
        event.accept()


def show_settings_editor():
    global settings_editor

    if settings_editor is None:
        settings_editor = SettingsEditor()
        settings_editor.show()
    else:
        settings_editor.raise_()
        settings_editor.activateWindow()
