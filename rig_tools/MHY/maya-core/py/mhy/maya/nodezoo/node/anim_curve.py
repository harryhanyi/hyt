"""
Nodezoo class for animation curves
"""
import maya.OpenMayaAnim as OpenMayaAnim
import maya.OpenMaya as OpenMaya
import maya.cmds as cmds
from mhy.maya.utils import undoable
from mhy.maya.nodezoo.node import DependencyNode
from mhy.maya.nodezoo.attribute import Attribute



class AnimCurve(DependencyNode):
    __NODETYPE__ = 'animCurve'
    __FNCLS__ = OpenMayaAnim.MFnAnimCurve

    class InputType(object):
        Time_Input = 2
        Unitless_Input = 3
        Unknown = 4

    TangentType = {
        OpenMayaAnim.MFnAnimCurve.kTangentGlobal: 'auto',
        OpenMayaAnim.MFnAnimCurve.kTangentLinear: 'linear',
        OpenMayaAnim.MFnAnimCurve.kTangentFlat: 'flat',
        OpenMayaAnim.MFnAnimCurve.kTangentSmooth: 'spline',
        OpenMayaAnim.MFnAnimCurve.kTangentClamped: 'clamped',
        OpenMayaAnim.MFnAnimCurve.kTangentPlateau: 'plateau',
        OpenMayaAnim.MFnAnimCurve.kTangentStepNext: 'stepnext',
    }

    class InfinityType(object):
        Constant = OpenMayaAnim.MFnAnimCurve.kConstant
        Linear = OpenMayaAnim.MFnAnimCurve.kLinear
        Cycle = OpenMayaAnim.MFnAnimCurve.kCycle
        Cycle_Relative = OpenMayaAnim.MFnAnimCurve.kCycleRelative
        Oscillate = OpenMayaAnim.MFnAnimCurve.kOscillate

    @classmethod
    def create_on_attribute(cls, attribute, *args, **kwargs):
        attribute = Attribute(attribute)
        cmds.setKeyframe(attribute.short_name, *args, **kwargs)
        source_node = attribute.source_node
        if not source_node:
            OpenMaya.MGlobal.displayError("Failed to create key frame on {}".format(attribute))
            return
        if source_node.type_name.startswith('animCurveT'):
            return source_node

    @property
    def input_type(self):
        if self.fn_node.isTimeInput():
            return AnimCurve.InputType.Time_Input
        elif self.fn_node.isUnitlessInput():
            return AnimCurve.InputType.Unitless_Input
        else:
            return AnimCurve.InputType.Unknown

    @property
    def attributes_to_export(self):
        return ['preInfinity', 'postInfinity', 'input', 'output']

    def export_additional_data(self):
        """
        Maya doesn't allow user set up key frames using plug directly so it has
        to be query and set through key frame api functions
        Returns:
            (list): data of keys frames
        """
        data = []
        x_util = OpenMaya.MScriptUtil(0.0)
        x_ptr = x_util.asFloatPtr()
        y_util = OpenMaya.MScriptUtil(0.0)
        y_ptr = y_util.asFloatPtr()
        for index in range(self.num_keys):
            key_data = dict()
            input_data = self.get_input(index)
            key_data['input'] = input_data
            value = self.get_value(index)
            key_data['value'] = value
            in_tangent_type = self.get_in_tangent_type(index)
            out_tangent_type = self.get_out_tangent_type(index)
            key_data['itt'] = in_tangent_type
            key_data['ott'] = out_tangent_type

            self.fn_node.getTangent(index, x_ptr, y_ptr, True)
            x = x_util.getFloat(x_ptr)
            y = y_util.getFloat(y_ptr)
            key_data['it'] = (x, y)

            self.fn_node.getTangent(index, x_ptr, y_ptr, False)
            x = x_util.getFloat(x_ptr)
            y = y_util.getFloat(y_ptr)
            key_data['ot'] = (x, y)

            data.append(key_data)
        return data

    def get_keys_data(self):
        """
        Fetch the key data in minimum format.
        Returns:
            dict: Key data dictionary. Key frame will be key of this dict
        """
        data = {}
        x_util = OpenMaya.MScriptUtil(0.0)
        x_ptr = x_util.asFloatPtr()
        y_util = OpenMaya.MScriptUtil(0.0)
        y_ptr = y_util.asFloatPtr()
        for index in range(self.num_keys):
            key_data = dict()
            input_data = self.get_input(index)
            value = self.get_value(index)
            key_data['value'] = value
            in_tangent_type = self.get_in_tangent_type(index)
            out_tangent_type = self.get_out_tangent_type(index)
            key_data['itt'] = in_tangent_type
            key_data['ott'] = out_tangent_type

            self.fn_node.getTangent(index, x_ptr, y_ptr, True)
            x = x_util.getFloat(x_ptr)
            y = y_util.getFloat(y_ptr)
            key_data['it'] = (x, y)

            self.fn_node.getTangent(index, x_ptr, y_ptr, False)
            x = x_util.getFloat(x_ptr)
            y = y_util.getFloat(y_ptr)
            key_data['ot'] = (x, y)

            data[input_data] = key_data
        return data

    @undoable
    def set_keys_data(self, data, merge=True, set_tangent_val=True):
        remaining_key = None
        if not merge:
            num_keys = self.num_keys
            if num_keys:
                for i in range(num_keys-1):
                    cmds.cutKey(self.name, index=(0, 0))
            remaining_key = self.get_keys()

        for idx, (key, key_data) in enumerate(data.items()):
            key = float(key)
            value = key_data.get('value')
            itt = key_data.get('itt')
            ott = key_data.get('ott')
            it = key_data.get('it')
            ot = key_data.get('ot')
            self.add_key(key, value, itt, ott)
            if set_tangent_val:
                locked = self.get_tangent_locked(key=key)
                self.set_tangent_locked(key=key, locked=locked)
                self.set_tangent(key=key, x=it[0], y=it[1], in_tangent=True)
                self.set_tangent(key=key, x=ot[0], y=ot[1], in_tangent=False)
                self.set_tangent_locked(key=key, locked=locked)

            # For the first iter, if remove remaining keys if necessary
            if idx == 0 and remaining_key is not None:
                for rem in remaining_key:
                    if abs(rem - key) > 0.001:
                        self.delete_key(rem)
                remaining_key = list()

    @undoable
    def load(self, data, make_connections=True, rename=False, replace=True):
        """
        Maya api only allows to set key frame data using specific command.
        Args:
            data:
            make_connections:
            rename:
            replace(bool): If remove existing keys

        Returns:

        """
        DependencyNode.load(self, data, make_connections, rename)
        remaining_key = None
        if replace:
            num_keys = self.num_keys
            if num_keys:
                for i in range(num_keys-1):
                    cmds.cutKey(self.name, index=(0, 0))
            remaining_key = self.get_keys()

        keys_data = data.get('additional', [])
        for idx, key_data in enumerate(keys_data):
            input_data = float(key_data.get('input'))
            value = key_data.get('value')
            itt = key_data.get('itt')
            ott = key_data.get('ott')
            it = key_data.get('it')
            ot = key_data.get('ot')
            self.add_key(input_data, value, itt, ott)
            locked = self.get_tangent_locked(key=input_data)
            self.set_tangent_locked(key=input_data, locked=locked)
            self.set_tangent(key=input_data, x=it[0], y=it[1], in_tangent=True)
            self.set_tangent(key=input_data, x=ot[0], y=ot[1], in_tangent=False)
            self.set_tangent_locked(key=input_data, locked=locked)

            # For the first iter, if remove remaining keys if necessary
            if idx == 0 and remaining_key is not None:
                for rem in remaining_key:
                    if abs(rem - input_data) > 0.001:
                        self.delete_key(rem)
                remaining_key = list()

    def delete_key(self, key):
        """
        Remove the key at given input value
        Args:
            key(float): The input value at which the key will be removed

        """
        if self.input_type == AnimCurve.InputType.Unitless_Input:
            cmds.cutKey(self.name, float=(key, key))
        elif self.input_type == AnimCurve.InputType.Time_Input:
            cmds.cutKey(self.name, time=(key, key))

    def clear_keys(self):
        """
        Clear all the keys. This method will delete the anim curve instance automatically
        thanks to maya

        """
        cmds.cutKey(self.name, clear=True)

    def add_key(self, key, value, in_tangent_type, out_tangent_type):
        """

        Args:
            key:
            value:
            in_tangent_type:
            out_tangent_type:

        Returns:

        """
        if isinstance(in_tangent_type, int):
            in_tangent_type = AnimCurve.TangentType.get(in_tangent_type, 'auto')
        if isinstance(out_tangent_type, int):
            out_tangent_type = AnimCurve.TangentType.get(out_tangent_type, 'auto')

        if self.input_type == AnimCurve.InputType.Unitless_Input:
            cmds.setKeyframe(
                self.name,
                float=key,
                value=value,
                inTangentType=in_tangent_type,
                outTangentType=out_tangent_type
            )
        elif self.input_type == AnimCurve.InputType.Time_Input:
            cmds.setKeyframe(
                self.name,
                time=key,
                value=value,
                inTangentType=in_tangent_type,
                outTangentType=out_tangent_type
            )

    def get_input(self, index):
        """
        Get the input value at a given index. Normally, input of animation curve is
        time unit. On the other hand, Set driven key is creating unit less input
        Args:
            index(int):

        Returns:

        """
        if self.input_type == AnimCurve.InputType.Unitless_Input:
            return self.fn_node.unitlessInput(index)
        elif self.input_type == AnimCurve.InputType.Time_Input:
            return self.fn_node.time(index).value()

    def get_value(self, index):
        """
        Get the value of the key at given index
        Args:
            index:

        Returns:

        """
        values = cmds.keyframe(self.name, index=(index, index), valueChange=True, query=True)
        return values[0]

    def find_closest_out_value(self, input_value):
        """
        Get the output value associated with the closest key frame
        Args:
            input_value(float): Look for a key closest to given input value

        Returns:
            float:
        """
        idx = self.fn_node.findClosest(input_value)
        return self.get_value(idx)

    def get_in_tangent_type(self, index, ):
        """
        Get the in-tangent type at index
        Args:
            index(int): Index number

        Returns:
            int:  Enum value for tangent type

        """
        return self.fn_node.inTangentType(index)

    def get_out_tangent_type(self, index):
        """
        Get the out-tangent type at index
        Args:
            index(int): Index number

        Returns:
            int: Enum value for tangent type

        """
        return self.fn_node.outTangentType(index)

    def get_tangent(self, index, in_tangent=True):
        """
        Get the tangent data at given index
        Args:
            index(int): The index number
            in_tangent(bool): If query in-tangent or not(out-tangent)

        Returns:
            tuple: x and y component of the tangent

        """
        x_util = OpenMaya.MScriptUtil(0.0)
        x_ptr = x_util.asFloatPtr()
        y_util = OpenMaya.MScriptUtil(0.0)
        y_ptr = y_util.asFloatPtr()
        self.fn_node.getTangent(index, x_ptr, y_ptr, in_tangent)
        x = x_util.getFloat(x_ptr)
        y = y_util.getFloat(y_ptr)
        return x, y

    def set_tangent(self, index=None, key=None, x=None, y=None, in_tangent=True):
        """
        Set tangent x and y value at given index for either in-tangent or out-tangent
        Args:
            index(int):
            key(int or float)
            x(float):
            y(float):
            in_tangent(bool): If set on in-tangent or not(out-tangent)

        """
        assert not (index is None and key is None), "Cannot specify both an index and a time"

        if in_tangent:
            kwarg = {
                "ix": x,
                "iy": y
            }
        else:
            kwarg = {
                "ox": x,
                "oy": y
            }
        if index is not None:
            kwarg['index'] = (index, index)
        elif self.input_type == AnimCurve.InputType.Unitless_Input:
            kwarg['float'] = (key, key)
        else:
            kwarg['time'] = (key, key)
        cmds.keyTangent(self.name, **kwarg)

    def get_tangent_locked(self, index=None, key=None):
        """
        Get the lock state of the keyframe at a given index
        Args:
            index(int): Index number
            key(float or int)

        Returns:
            bool: If the tangent is locked at given index

        """
        if index is None and key is not None:
            index = self.fn_node.findClosest(float(key))
        return self.fn_node.tangentsLocked(index)

    def set_tangent_locked(self, index=None, key=None, locked=True):
        """
        Set the lock state of the keyframe at a given index
        Args:
            index(int or None): Index number
            key(float or None): The input value
            locked(bool): lock state to set

        """
        assert not (index is None and key is None), "Cannot specify both an index and a time"
        if index is not None:
            cmds.keyTangent(self.name, lock=locked, index=(index, index))
        elif self.input_type == AnimCurve.InputType.Unitless_Input:
            cmds.keyTangent(self.name, lock=locked, float=(key, key))
        else:
            cmds.keyTangent(self.name, lock=locked, time=(key, key))

    @property
    def num_keys(self):
        """
        Get the number of key
        Returns:
            int: The number of keys

        """
        return self.fn_node.numKeys()

    def get_keys(self):
        """
        GEt the input keys in index order
        Returns:
            list: Input keys
        """
        keys = list()
        for idx in range(self.num_keys):
            key = self.get_input(idx)
            keys.append(key)

        return keys


class AnimCurveTA(AnimCurve):
    __NODETYPE__ = 'animCurveTA'


class AnimCurveTL(AnimCurve):
    __NODETYPE__ = 'animCurveTL'


class AnimCurveTT(AnimCurve):
    __NODETYPE__ = 'animCurveTT'


class AnimCurveTU(AnimCurve):
    __NODETYPE__ = 'animCurveTU'


class AnimCurveUA(AnimCurve):
    __NODETYPE__ = 'animCurveUA'


class AnimCurveUL(AnimCurve):
    __NODETYPE__ = 'animCurveUL'


class AnimCurveUU(AnimCurve):
    __NODETYPE__ = 'animCurveUU'


class AnimCurveUnknown(DependencyNode):
    __NODETYPE__ = 'animCurveUnknown'





