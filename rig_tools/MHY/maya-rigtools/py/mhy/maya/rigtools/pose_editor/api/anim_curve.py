"""
The Influence class represents the pose drivens.
"""
from decimal import Decimal
from maya.api import OpenMayaAnim
from mhy.maya.rigtools.pose_editor.api.utils import get_anim_curve_fn


class AnimCurve(object):
    """
    AnimCurve object to provide functions for io, copy paste, mirror etc.
    """

    def __init__(self, curve_node_name):
        self.node_name = curve_node_name

    def get_data(self, keys_range):
        """
        Get a dictionary with all the information of the MFnAnimCurve
        """
        data = dict()
        anim_curve_fn = get_anim_curve_fn(self.node_name)
        if not anim_curve_fn:
            return {}
        for index in range(anim_curve_fn.numKeys):
            key = anim_curve_fn.input(index)
            value = anim_curve_fn.value(index)
            if keys_range and (key < keys_range[0] or key > keys_range[1]):
                continue
            tit = anim_curve_fn.inTangentType(index)
            tot = anim_curve_fn.outTangentType(index)
            # linear tangent is the default tangent.
            if tit == OpenMayaAnim.MFnAnimCurve.kTangentLinear and tot == OpenMayaAnim.MFnAnimCurve.kTangentLinear:
                data[key] = {'v': value}
            else:
                data[key] = {'v': value, 'tt': [tit, tot]}
        return data

    def load(self, data, keys_range):
        """
        update the AnimCurve node from a dictionary.
        """
        anim_curve_fn = get_anim_curve_fn(self.node_name)
        keys = []
        for key_pos, key_data in data.items():
            key = Decimal(key_pos)
            # Then we round it to 2 places
            key = round(key, 2)
            value = key_data.get('v')
            if value is None:
                continue
            if keys_range and (key < keys_range[0] or key > keys_range[1]):
                continue
            value = float(value)
            # linear tangent is equal to 2, which is default.
            tit, tot = key_data.get('tt', [OpenMayaAnim.MFnAnimCurve.kTangentLinear,
                                           OpenMayaAnim.MFnAnimCurve.kTangentLinear])
            anim_curve_fn.addKey(
                key, value, tangentInType=tit, tangentOutType=tot)
            keys.append(key)
        return sorted(keys)
