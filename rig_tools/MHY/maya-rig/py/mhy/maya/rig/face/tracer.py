import maya.cmds as cmds

from mhy.maya.standard.name import NodeName
from mhy.maya.nodezoo.node import Node
import mhy.maya.maya_math as mmath


TRACER_POINTS = (
    (0.0, -0.06971326875686645),
    (0.008717686450986578, -0.03253484659916775),
    (0.03485663437843323, -0.06037346248626707),
    (0.02381717249751092, -0.02381717249751092),
    (0.06037346248626707, -0.03485663437843323),
    (0.03253484659916775, -0.008717686450986578),
    (0.06971327463785806, 0.0),
    (0.03253484659916775, 0.008717686450986578),
    (0.06037346248626707, 0.03485663437843323),
    (0.02381717249751092, 0.02381717249751092),
    (0.03485663437843323, 0.06037346248626707),
    (0.008717686450986578, 0.03253484659916775),
    (0.0, 0.06971326875686645),
    (-0.008717686450986578, 0.03253484659916775),
    (-0.03485663437843323, 0.06037346248626707),
    (-0.02381717249751092, 0.02381717249751092),
    (-0.06037346248626707, 0.03485663437843323),
    (-0.03253484659916775, 0.008717686450986578),
    (-0.06971327463785806, 0.0),
    (-0.03253484659916775, -0.008717686450986578),
    (-0.06037346248626707, -0.03485663437843323),
    (-0.02381717249751092, -0.02381717249751092),
    (-0.03485663437843323, -0.06037346248626707),
    (-0.008717686450986578, -0.03253484659916775),
    (0.0, -0.06971326875686645))


class ParameterTracer():
    """
    TODO doc
    """

    def __init__(
            self, param_patch, name='XXX', base_influence=None,
            diameter_ratio=.05, scale_ratio=(1.0, 1.0), shape_color=31):
        """TODO doc"""
        self.tracer = name
        self.param_patch = Node(param_patch)
        self.patch_shape = self.param_patch.get_shapes()[0]
        self.base_influence = Node(base_influence) if base_influence else None
        self.diameter_ratio = diameter_ratio
        self.scale_ratio = scale_ratio
        self.shape_color = shape_color

        self.diameter = None

    def create(self):
        """TODO doc"""
        tracer_shape = Node.create(
            'nurbsCurve',
            self.param_patch,
            TRACER_POINTS,
            name=self.tracer,
            degree=1)
        self.tracer = tracer_shape.get_parent()

        self.get_tracer_diameter()
        self.get_tracer_scale_ratio()
        self.set_tracer_scale()
        self.add_parameter_attributes()
        self.cleanup()

        if self.base_influence:
            self.base_influence_constraint()
            return self.tracer, self.base_influence
        else:
            return self.tracer

    def get_tracer_diameter(self):
        """TODO doc"""
        size = mmath.get_object_size(self.param_patch)
        self.diameter = sum(size) * self.diameter_ratio

    def get_tracer_scale_ratio(self):
        """TODO doc"""
        arcd = Node(cmds.arcLengthDimension('{}.u[1]'.format(self.patch_shape)))
        arcU = arcd.arcLength.value
        arcd.uParamValue.value = 0
        arcd.vParamValue.value = 1
        arcV = arcd.arcLengthInV.value
        cmds.delete(arcd.get_parent())
        self.scale_ratio = (1.0 / arcU, 1.0 / arcV)

    def set_tracer_scale(self):
        """TODO doc"""
        cmds.scale(
            self.diameter * self.scale_ratio[0],
            self.diameter * self.scale_ratio[1],
            1.0,
            self.tracer)
        self.tracer.make_identity(apply=True, scale=True)

    def add_parameter_attributes(self):
        """TODO doc"""
        self.tracer.translateX.alias = 'parameterU'
        self.tracer.translateY.alias = 'parameterV'

        for attr in ('originU', 'originV'):
            self.tracer.add_attr('float', name=attr, keyable=False)

    def cleanup(self):
        """TODO doc"""
        self.tracer.lock('tzrsv')
        self.tracer.set_color(color=self.shape_color, shape=True)
        self.tracer.sync_shape_name()

    def base_influence_constraint(self):
        """TODO doc"""
        cpos = Node.create('closestPointOnSurface')
        self.patch_shape.worldSpace[0] >> cpos.inputSurface

        name = NodeName(self.base_influence, ext='FLCTRANSFORM')
        flc = Node.create('follicle', self.patch_shape, name=name)
        flc.name = name.replace_ext('FLC')
        flc_pin = Node.create('transform', name=name.replace_ext('FLCPIN'))

        pos = self.base_influence.get_translation(space='world')
        for ax, pos in zip('XYZ', pos):
            cpos.set_attr('inPosition' + ax, pos)
        u = cpos.parameterU.value
        v = cpos.parameterV.value

        tracer_han.parameterU >> flc.parameterU
        tracer_han.parameterV >> flc.parameterV
        tracer_han.parameterU.value = u
        tracer_han.parameterV.value = v

        for ax in 'XYZ':
            flc.attr('outTranslate' + ax) >> flc_pin.attr('translate' + ax)
            flc.attr('outRotate' + ax) >> flc_pin.attr('rotate' + ax)

        self.base_influence.constrain('parent', flc_pin, maintainOffset=True)
        cmds.delete(cpos)
        