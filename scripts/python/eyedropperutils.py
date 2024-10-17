import hou


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
