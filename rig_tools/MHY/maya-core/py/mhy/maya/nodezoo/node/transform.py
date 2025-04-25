"""
This modules contains api for Transform node
"""
import math

from maya import cmds, OpenMaya

from mhy.maya.nodezoo.node import Node, DagNode


ROTATE_ORDER = {
    'xyz': 0,
    'yzx': 1,
    'zxy': 2,
    'xzy': 3,
    'yxz': 4,
    'zyx': 5
}


def resolve_xform_attr_string(attr_string, skip_parent=False, skip_vis=False):
    """Resolves an attribute string to a list of attributes.
    Supported attributes are: t, r, s, v.
    e.g. "trxsy" >> ["t", "tx", "ty", "tz", "rx", "sy"]

    Args:
        attr_string (str): An attribute string to resolve.
        skip_parent (bool): If False, include parent attibutes (t, r ,s)
            if all children attrs are in the attrstring.
            Otherwise skip parent attibutes completely.
        skip_vis (bool): If True, skip the visibility attribute.

    Returns:
        list: A list of resolved attributes.
    """
    if not attr_string:
        return []

    attr_string = attr_string.lower()
    if attr_string == 'all':
        attr_string = 'trsv'

    attrs = {'t': '', 'r': '', 's': ''}
    itr_attrs = []
    length = len(attr_string)
    for i in range(length):
        cur = attr_string[i]
        if cur in 'xyz':
            continue
        elif cur == 'v':
            if not skip_vis:
                itr_attrs.append('v')
            continue

        if i < length - 1:
            n = attr_string[i + 1]
            if n in 'xyz':
                attrs[cur] += n
            else:
                attrs[cur] = 'xyz'
        else:
            attrs[cur] = 'xyz'

    for key, val in attrs.items():
        for ax in val:
            itr_attrs.append(key + ax)
        if not skip_parent and len(val) == 3:
            itr_attrs.append(key)

    itr_attrs.sort()
    return itr_attrs


class Transform(DagNode):
    """
    Transform node class.
    """

    __NODETYPE__ = 'transform'
    __FNCLS__ = OpenMaya.MFnTransform

    @classmethod
    def create(cls, name='transform', parent=None):
        xform = cls(cmds.createNode('transform', name=name))
        if parent:
            xform.set_parent(parent)
        return xform

    def get_matrix(
            self, space='object', inverse=False,
            as_transform=True, as_tuple=True):
        """Retrieve the transformation matrix.

        Args:
            space (str): transform space in which to retrieve the matrix:
                object, world, or parent
            inverse (bool): Returns an inversed matrix.
            as_transform (bool): If True and as_tuple is False, returns a
                MTransformationMatrix. Otherwise returns MMatrix.
            as_tuple (bool): If True, return a tuple,
                otherwise return MTransformationMatrix.

        Returns: tuple, MMatrix, or MTransformationMatrix
        """
        if space == 'world':
            attr = 'worldMatrix'
        elif space == 'object':
            attr = 'matrix'
        elif space == 'parent':
            attr = 'parentMatrix'
        else:
            raise ValueError('Invalid space: {}'.format(space))
        matrix = cmds.getAttr('{}.{}'.format(self.name, attr))

        if as_tuple and not inverse:
            return matrix

        matrix = OpenMaya.MMatrix(matrix)
        if inverse:
            matrix = matrix.inverse()

        if not as_tuple:
            if as_transform:
                return OpenMaya.MTransformationMatrix(matrix)
            return matrix
        return tuple(matrix.as_tuple())

    def set_matrix(self, matrix, space='object', inverse=False):
        """Sets the transformation matrix.

        Args:
            matrix(list or MMatrix): A MMatrix or a list of matrix values.
            space (str): transform space in which to retrieve the matrix:
                object or world
            inverse (bool): If True, inverse the matrix before setting it.

        Returns:
            None
        """
        if isinstance(matrix, (list, tuple)):
            matrix = OpenMaya.MMatrix(matrix)
        elif isinstance(matrix, OpenMaya.MTransformationMatrix):
            matrix = matrix.asMatrix()
        if inverse:
            matrix = matrix.inverse()
        matrix = matrix.as_tuple()

        if space == 'object':
            cmds.xform(self.long_name, objectSpace=True, matrix=matrix)
        elif space == 'world':
            cmds.xform(self.long_name, worldSpace=True, matrix=matrix)
        else:
            raise ValueError('Invalid space: {}'.format(space))

    def get_translation(self, space='object', as_tuple=True):
        """Retrieve the translation component of this transformation
        in linear units.

        Args:
            space (str): transform space in which to retrieve the translation:
                object, world, or parent
            as_tuple (bool): If True, return a tuple, otherwise return MVector.

        Returns:
            tuple or MVector: The translation vector.
        """
        vec = self.get_matrix(
            space, as_transform=True, as_tuple=False).getTranslation(OpenMaya.MSpace.kWorld)
        if as_tuple:
            return vec[0], vec[1], vec[2]
        return vec

    def set_translation(self, vector, space='object'):
        """Sets the translation component of this transformation.

        Args:
            vector (list or MVector): The translation vector.
            space (str): transform space in which to set the translation:
                object or world

        Returns: None
        """
        if not isinstance(vector, (list, tuple)):
            vector = (vector[0], vector[1], vector[2])
        if space == 'object':
            cmds.xform(self.long_name, objectSpace=True, translation=vector)
        elif space == 'world':
            cmds.xform(self.long_name, worldSpace=True, translation=vector)

    def get_rotation(self, space='object', as_tuple=True):
        """Retrieve the rotation component of this transformation.

        Args:
            space (str): transform space in which to retrieve the rotation:
                object, world, or parent
            as_tuple (bool): If True, return a tuple,
                otherwise return MEulerRotation.

        Returns:
            tuple or MEulerRotation: The euler rotation.
        """
        rot = self.get_matrix(
            space, as_transform=True, as_tuple=False).eulerRotation()
        # rot.reorderIt(self.get_rotate_order())
        if as_tuple:
            return tuple([math.degrees(rot[i]) for i in range(3)])
        return rot

    def set_rotation(self, rot, space='object'):
        """Sets the rotation component of this transformation.

        Args:
            rot (list or MEulerRotation): The euler rotation.
            space (str): transform space in which to set the rotation:
                object or world

        Returns: None
        """
        if not isinstance(rot, (list, tuple)):
            rot = (rot[0], rot[1], rot[2])
        if space == 'object':
            cmds.xform(self.long_name, objectSpace=True, rotation=rot)
        elif space == 'world':
            cmds.xform(self.long_name, worldSpace=True, rotation=rot)
        else:
            raise ValueError('Invalid space: {}'.format(space))

    def get_rotation_quaternion(self, space='object'):
        """
        Retrieve the rotation component of this transformation as a quaternion.
        Args:
            space(str): transform space in which to set the rotation:
                object or world

        Returns:
            tuple: x, y, z, w components of the quaternion

        """
        x = OpenMaya.MScriptUtil().asDoublePtr()
        y = OpenMaya.MScriptUtil().asDoublePtr()
        z = OpenMaya.MScriptUtil().asDoublePtr()
        w = OpenMaya.MScriptUtil().asDoublePtr()
        if space == 'world':
            self.fn_node.getRotationQuaternion(
                x,
                y,
                z,
                w,
                OpenMaya.MSpace.kWorld)
        else:
            self.fn_node.getRotationQuaternion(x, y, z, w)

        x = OpenMaya.MScriptUtil().getDouble(x)
        y = OpenMaya.MScriptUtil().getDouble(y)
        z = OpenMaya.MScriptUtil().getDouble(z)
        w = OpenMaya.MScriptUtil().getDouble(w)
        return x, y, z, w

    def set_rotation_quaternion(self, x, y, z, w, space='object'):
        """
        Change the rotation component of this transformation using a quaternion

        Args:
            x(float): x component of the quaternion
            y(float): y component of the quaternion
            z(float): z component of the quaternion
            w(float): w component of the quaternion
            space(str): transform space in which to set the rotation:
                object or world

        """

        if space == 'world':
            self.fn_node.setRotationQuaternion(
                x,
                y,
                z,
                w,
                OpenMaya.MSpace.kWorld
            )
        else:
            self.fn_node.setRotationQuaternion(x, y, z, w)

    def get_scale(self, space='object', as_tuple=True):
        """Retrieve the scale component of this transformation.

        Args:
            space (str): transform space in which to retrieve the scale:
                object, world, or parent
            as_tuple (bool): If True, return a tuple,
                otherwise return MVector.

        Returns:
            tuple or MVector: The scale values.
        """
        mat = self.get_matrix(space, as_transform=True, as_tuple=False)
        util = OpenMaya.MScriptUtil()
        util.createFromDouble(0, 0, 0)
        ptr = util.asDoublePtr()
        mat.getScale(ptr, OpenMaya.MSpace.kWorld)
        scale = [
            util.getDoubleArrayItem(ptr, 0),
            util.getDoubleArrayItem(ptr, 1),
            util.getDoubleArrayItem(ptr, 2)]
        if as_tuple:
            return scale
        return OpenMaya.MVector(*scale)

    def set_scale(self, scale, space='object'):
        """Sets the rotation component of this transformation.

        Args:
            rot (list or MEulerRotation): The euler rotation.
            space (str): transform space in which to set the rotation:
                object or world

        Returns: None
        """
        if not isinstance(scale, (list, tuple)):
            scale = (scale[0], scale[1], scale[2])
        if space == 'object':
            cmds.xform(self.long_name, objectSpace=True, scale=scale)
        elif space == 'world':
            cmds.xform(self.long_name, worldSpace=True, scale=scale)
        else:
            raise ValueError('Invalid space: {}'.format(space))

    def lock(self, attrs='all'):
        """Locks and hides specified TRSV attributes.

        Args:
            attrs (str): A string combination of xform channels to lock.
                Supported channels are: t, r, s, v,
                tx, ty, tz, rx, ry, rz, sx, sy, sz.
                If "all", include all channels.
        """
        for attr in resolve_xform_attr_string(attrs):
            attr = self.attr(attr)
            attr.keyable = False
            attr.locked = True
            attr.channelBox = False

    def unlock(self, attrs='all'):
        """Unlocks specified TRSV attributes.

        Args:
            attrs (str): A string combination of xform channels to unlock.
                Supported channels are: t, r, s, v,
                tx, ty, tz, rx, ry, rz, sx, sy, sz.
                If "all", include all channels.
        """
        for attr in resolve_xform_attr_string(attrs):
            attr = self.attr(attr)
            attr.keyable = True
            attr.locked = False
            parent = attr.parent
            if parent:
                parent.keyable = True
                parent.locked = False

    def reset(self, attrs='trs'):
        """Resets the specified transform channels.

        Args:
            attrs (str): A string combination of xform channels to reset.
                Supported channels are: t, r, s,
                tx, ty, tz, rx, ry, rz, sx, sy, sz.
                If "all", include all channels.
        """
        # self.unlock()
        for attr in resolve_xform_attr_string(attrs, skip_vis=True):
            value = 1 if attr.startswith('s') else 0
            if len(attr) == 1:
                value = (value, value, value)
            self.set_attr(attr, value)

    def get_rotate_order(self):
        """Returns the rotation order.
        Returns: int
        """
        return self.rotateOrder.value

    def set_rotate_order(self, order):
        """Sets the rotation order.

        Args:
            order (str or int): The rotation order index or string.

        Returns: None
        """
        if not isinstance(order, int):
            order = ROTATE_ORDER.get(order.lower(), 0)
        cmds.setAttr('{}.rotateOrder'.format(self.long_name), order)

    def set_limit(self, **kwargs):
        """Sets the transform limit.

        Args:
            kwargs (dict): Keyword arguments accepted by cmds.transformLimits()
        """
        cmds.transformLimits(self.long_name, **kwargs)

    def duplicate(self, rotate_order=None, unlock=True, **kwargs):
        """Duplicates this transform node.

        Args:
            rotate_order (str): A rotate order to apply to the duplicated node.
                If None, use this transform's rotate order.
            kwargs: Keyword argument accepted by cmds.duplicate().

        Returns:
            list: The duplicated nodes.
        """
        nodes = DagNode.duplicate(self, **kwargs)
        if rotate_order is None:
            rotate_order = self.get_attr('rotateOrder')
        for node in nodes:
            node.set_rotate_order(rotate_order)
            # clear intermediate shapes
            for shape in node.get_shapes(intermediate=True):
                if shape.is_intermediate:
                    cmds.delete(shape)
            if unlock:
                node_attrs = node.unlock('trsv')
        return nodes

    def constrain(self, typ, *args, **kwargs):
        """Constrains this transform to one or more target transforms.

        Args:
            typ (str): The constraint type.
                e.g. point, orient, parent, poleVector, etc.
            args (str or Transform): One or more target transform nodes
            kwargs: keyword arguments accepted by cmds.xxxConstraint()

        Returns:
            Node: The constraint node.
        """
        args = list(args) + [self.long_name]
        cns = getattr(cmds, '{}Constraint'.format(typ))(*args, **kwargs)
        return Node(cns[0])

    def align(self, *args, **kwargs):
        """
        Aligns this transform to one or more target transforms.

        Args:
            args (str or Transform): One or more target transform nodes
            kwargs:
                skipTranslate (str or bool): A string indicating translation
                    axis to ignore. e.g. 'xy'.
                    Use bool to skip/unskip all channels.
                skipRotate (str or bool): A string indicating rotation
                    axis to ignore. e.g. 'xy'.
                    Use bool to skip/unskip all channels.
                constraint (bool): If True, keep the constraint node.

        Returns: None
        """
        skipTranslate = kwargs.get('skipTranslate', False)
        skipRotate = kwargs.get('skipRotate', False)
        constraint = kwargs.get('constraint', False)

        # convert arguments to Maya format
        if skipTranslate is True:
            skipTranslate = 'xyz'
        if skipRotate is True:
            skipRotate = 'xyz'
        skipTranslate = list(skipTranslate) if skipTranslate else 'none'
        skipRotate = list(skipRotate) if skipRotate else 'none'

        # make a constraint accordingly
        kwargs = {'maintainOffset': False}
        if set(skipTranslate) == set('xyz'):
            kwargs['skip'] = skipRotate
            cns = self.constrain('orient', *args, **kwargs)
        elif set(skipRotate) == set('xyz'):
            kwargs['skip'] = skipTranslate
            cns = self.constrain('point', *args, **kwargs)
        else:
            kwargs['skipTranslate'] = skipTranslate
            kwargs['skipRotate'] = skipRotate
            cns = self.constrain('parent', *args, **kwargs)

        # delete the constraint
        if not constraint:
            cmds.delete(cns)

    def parent_align(self, target, keep_new_parent=False):
        """Snaps this transform to a target transform via parenting.

        Args:
            target (str or Transform): A transform node or its name.
            keep_new_parent (bool): If True, leaves this node under target.

        Returns: None
        """
        cur_parent = self.get_parent()
        self.set_parent(target)
        self.reset()
        if not keep_new_parent:
            self.set_parent(cur_parent)

    def make_identity(self, **kwargs):
        """Wrapper around cmds.makeIdentity()."""
        cmds.makeIdentity(self.long_name, **kwargs)

    def add_parent(self, name=None, attrs='trs'):
        """Adds a parent transform on top of this node.

        Args:
            name (str): Name of the new parent node.
            attrs (str): A string combination of xform channels
                to transfer values from this node to the new parent.
                Supported channels are: t, r, s,
                tx, ty, tz, rx, ry, rz, sx, sy, sz.
                If "all", include all channels.

        Returns:
            Transform: The new parent node object.
        """
        cur_parent = self.get_parent()
        if not name:
            name = self.name + '_parent'
        new_parent = Node(cmds.group(empty=True, name=name))
        if cur_parent:
            new_parent.set_parent(cur_parent)
            new_parent.reset()
        self.set_parent(new_parent)

        # transfer xform value to the new parent
        for attr in resolve_xform_attr_string(attrs, skip_vis=True):
            val = self.get_attr(attr)
            new_parent.set_attr(attr, val)

        # reset channels on this node
        self.reset(attrs)
        return new_parent

    def add_child(self, name=None, align=True, insert=True):
        """Adds a child transform under of this node.

        Args:
            name (str): Name of the new child node.
            relative (bool): If True, align new child to this node.
            insert (bool): If True, all current child transforms will
                be parented under the new child node.

        Returns:
            Transform: The new child node object.
        """
        if not name:
            name = self.name + '_child'
        if insert:
            cur_children = self.get_children(type_='transform')
        new_child = Transform.create(name=name)
        new_child.set_parent(self)
        if align:
            new_child.reset()
        if insert and cur_children:
            cmds.parent(cur_children, new_child)
        return new_child

    def add_annotation(self, other, text=None, display_type='normal'):
        """Adds an annotation shape that points from this transform
        to another.

        Args:
            other (Transform): The transform this annotation points at.
            text (str): Some text to display.
            display_type (str): Display type, "template" or "reference".

        Returns:
            DagNode: The the annotation shape node.
        """
        other = Node(other)

        # get the locator under other, create a new one if not found
        loc = other.get_children(exact_type='locator')
        if loc:
            loc = loc[0]
        else:
            loc = Node(cmds.createNode('locator'))
            loc_xform = loc.get_parent()
            loc.set_parent(other)
            loc_xform.delete()
            loc.hide()
            other.sync_shape_name()

        # create the annotation shape
        ann = Node(cmds.createNode('annotationShape'))
        ann_xform = ann.get_parent()
        cmds.connectAttr(
            loc.name + '.worldMatrix[0]',
            ann.name + '.dagObjectMatrix[0]')

        if display_type == 'template':
            ann.overrideEnabled.value = True
            ann.overrideDisplayType.value = 1
        elif display_type == 'reference':
            ann.overrideEnabled.value = True
            ann.overrideDisplayType.value = 2
        if text:
            ann.text.value = str(text)

        ann.set_parent(self)
        self.sync_shape_name()
        ann_xform.delete()

        return ann

    def get_distance_to(self, other, space='world'):
        """
        Get the distance to another transform node in a given space
        Args:
            other(Transform or str): Another object
            space(str):

        Returns:
            float
        """
        if not isinstance(other, Transform):
            other = Transform(other)
        assert isinstance(other, Transform), "Failed cast other into a transform node".format(other)

        this_translation = self.get_translation(space=space, as_tuple=False)

        other_translation = other.get_translation(space=space, as_tuple=False)

        return (this_translation - other_translation).length()

    def set_transform_limits(self, *args, **kwargs):
        """
        The transformLimits command allows us to set, edit, or query the limits
        of the transformation that can be applied to this transform node.
        Args:
            *args:
            **kwargs:

        """
        cmds.transformLimits(self.name, *args, **kwargs)

    def remove_transform_limits(self):
        """
        turn all the limits off and reset them to their default values
        """
        cmds.transformLimits(self.name, remove=True)

    def get_open_xform_attrs(self):
        """Returns a string representing the open xform attributes."""
        open_attrs = ''
        for attr in 'trs':
            for ax in 'xyz':
                at = '{}.{}{}'.format(self, attr, ax)
                if not cmds.getAttr(at, lock=True) and \
                   cmds.getAttr(at, settable=True):
                    open_attrs += attr
                    break
        return open_attrs
