import json
from dataclasses import asdict, dataclass, field, fields, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import hou
from PySide2.QtCore import Qt
from PySide2.QtWidgets import QComboBox, QHBoxLayout, QLabel, QMainWindow, QVBoxLayout, QWidget

user_pref_dir = Path(hou.getEnvConfigValue("HOUDINI_USER_PREF_DIR"))
settings_file = user_pref_dir / "h-color-picker.json"


def _strip_unused_keys(data_class: type, d: dict[str, Any]) -> dict[str, Any]:
    field_names = [f.name for f in fields(data_class)]
    return {key: d[key] for key in d if key in field_names}


def _from_dict(data_class: type, d: dict[str, Any] | Any) -> Any:
    if is_dataclass(data_class):
        field_types = {f.name: f.type for f in fields(data_class)}
        stripped_dict = _strip_unused_keys(data_class, d)
        return data_class(**{f: _from_dict(field_types[f], d[f]) for f in stripped_dict})
    return d


class NonOcioTransform(str, Enum):
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


settings: Settings = Settings()


def load_settings():
    if not settings_file.exists():
        return

    global settings

    try:
        with open(settings_file, "r") as file:
            json_dict = json.load(file)
            settings = _from_dict(Settings, json_dict)
    except Exception as e:
        settings = Settings()
        pass


def save_settings():
    json_string = json.dumps(asdict(settings), indent=2)
    with open(settings_file, "w") as file:
        file.write(json_string)


class HouIcon(QLabel):
    def __init__(self, icon_name: str, size=32, parent: QWidget | None = None):
        super().__init__(parent)
        icon = hou.qt.Icon(icon_name)
        if icon is not None:
            self.setPixmap(icon.pixmap(size, size))


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
        label.setFixedWidth(100)
        label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        layout.addWidget(label)

        layout.addWidget(HouIcon("KEYS_LMB"))

        separator = QLabel("<b><font size=12> : </font></b>")
        layout.addWidget(separator)

        source_space_selector = OcioSpaceSelector(target.source_space)
        source_space_selector.currentTextChanged.connect(lambda t: target.set_source_space(t))

        dest_space_selector = OcioSpaceSelector(target.dest_space)
        dest_space_selector.currentTextChanged.connect(lambda t: target.set_dest_space(t))

        layout.addWidget(source_space_selector)

        layout.addWidget(HouIcon("BUTTONS_forward"))
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

        layout.addWidget(TransformSettingsEditor(settings.transform, ""))
        layout.addWidget(
            TransformSettingsEditor(
                settings.transform_with_shift,
                "<b><font size=5>Shift + </font></b>",
            )
        )
        layout.addWidget(
            TransformSettingsEditor(
                settings.transform_with_control, "<b><font size=5>Ctrl + </font></b>"
            )
        )

    def closeEvent(self, event):
        global settings_editor
        settings_editor = None
        save_settings()
        event.accept()


def show_settings_editor():
    global settings_editor

    if settings_editor is None:
        settings_editor = SettingsEditor()
        settings_editor.show()
    else:
        settings_editor.raise_()
        settings_editor.activateWindow()
