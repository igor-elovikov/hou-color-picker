import hou
from PySide2.QtGui import QColor

from .settings import TransformSettings


def transform_color(
    color: QColor | hou.Color | tuple[float, ...], setting: TransformSettings
) -> tuple[float, float, float]:
    if isinstance(color, hou.Color):
        hcolor: hou.Color = color
    elif isinstance(color, QColor):
        hcolor = hou.qt.fromQColor(color)[0]
    else:
        hcolor: hou.Color = hou.Color(color)
    result = hcolor.ocio_transform(setting.source_space, setting.dest_space, "")
    return result.rgb()


def set_parm_color(parm: hou.Parm, color: hou.Color, transform: TransformSettings) -> None:
    result = transform_color(color, transform)

    if isinstance(parm, hou.ParmTuple) and len(parm) == 4:
        alpha = parm[3].eval()
        result = np.append(result, alpha)

    parm.set(result)


def is_color_ramp(parms):
    if not parms:
        return False
    parm = parms[0]  # type: hou.Parm
    parm_template = parm.parmTemplate()  # type: hou.ParmTemplate

    if (
        parm_template.type() == hou.parmTemplateType.Ramp
        and parm_template.parmType() == hou.rampParmType.Color
    ):
        return True

    return False


def is_color_parm(parms):
    if not parms:
        return False

    parm = parms[0]  # type: hou.Parm
    parm_template = parm.parmTemplate()  # type: hou.ParmTemplate

    if (
        parm_template.type() == hou.parmTemplateType.Float
        and (parm_template.numComponents() == 3 or parm_template.numComponents() == 4)
        and parm_template.namingScheme() == hou.parmNamingScheme.RGBA
    ):
        return True

    return False


def is_float_ramp(parms):
    if not parms:
        return False
    parm = parms[0]  # type: hou.Parm
    parm_template = parm.parmTemplate()  # type: hou.ParmTemplate

    if (
        parm_template.type() == hou.parmTemplateType.Ramp
        and parm_template.parmType() == hou.rampParmType.Float
    ):
        return True

    return False
