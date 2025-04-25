from maya import cmds, OpenMaya

from mhy.maya.nodezoo.node import Node, Transform, DagNode
from mhy.maya.standard.name import NodeName


import mhy.maya.rig.constants as const
import math


ATTR_SPACE = 'space'
IDEN_MAT_NODE = 'IDENTITY_MATRIX'


def _create_ctrl_groups(
        ctrl, group_exts=('PLC', 'SDK', 'OFFSET'), orient_node=None):
    """Creates a list of parent groups for a given ctrl.

    Args:
        ctrl (MHYCtrl): A ctrl transform object to work with.
        group_exts (tuple): A list of extensions used to create parent groups.
        orient_node (str): A node to orient the root group to.
            If None, orient to the ctrl transform.

    Returns:
        list: A list of group names.
    """
    name = NodeName(ctrl)
    k = name.ext.replace('CTRL', '')

    groups = []
    for i, ext in enumerate(group_exts):
        group = Node.create('transform', name=NodeName(name, ext=k + ext))
        if i > 0:
            group.set_parent(groups[i - 1])
        groups.append(group)

    if orient_node:
        groups[0].align(orient_node, skip_translate=True)
        groups[0].align(ctrl, skip_rotate=True)
    else:
        groups[0].align(ctrl)

    ctrl.set_parent(groups[-1])
    return groups


class MHYCtrl(Transform):
    """
    A class interfacing anim ctrls used in the MHY rigging system.
    """

    __CUSTOMTYPE__ = 'MHYCtrl'

    @classmethod
    def create(
            cls, name=None, xform=None,
            pos=(0, 0, 0), rot=(0, 0, 0), scale=(1, 1, 1), color=None,
            shape='circle', ext=None, rot_order=None, limb_root=None,
            group_exts=('PLC', 'SDK', 'OFFSET')):
        """Builds a MHY ctrl.

        Args:
            name (str): Name of the ctrl.
            xform (str): A transform node to snap this ctrl to.
                If None, create it at world origin.
                If arg "name" is None, the inherit this xform's name.
            pos (tuple): Ctrl's local position.
            rot (tuple): Ctrl's local rotation.
            scale (tuple): Local scale of the ctrl shape.
                It's a list of xyz value input, default is (1, 1, 1).
                Useful for creating non-proportional ctrl shapes.
            color (tuple): The RGB value of the ctrl color.
                If None, use default color based on the "side" token in
                the ctrl name.
            shape (str): The shape name of this ctrl.
            ext (str): If not None, override the extension(type) of this ctrl.
                Valid ext must ends with "CTRL".
            rot_order (int): The rotate order of this ctrl and all its offsets.
                If None and xform is provided, use the xform's rotate order.
            limb_root (MHYLimbRoot): A limb root node to connect this ctrl to.
            group_exts (list): A list of parent group extensions to create.

        Returns: MHYCtrl
            The ctrl object.
        """
        # convert xform to a Node object
        if xform:
            xform = Node(xform)

        # get ctrl name
        name = NodeName(name) if name else None
        if xform and not name:
            name = NodeName(xform)
        if not name:
            raise ValueError('Need to privode either a name or a transform!')
        if ext:
            name = name.replace_ext(ext)
        # if not name.endswith('CTRL'):
        #     raise ValueError('Invalid ctrl extension: {}'.format(name.ext))
        if cmds.objExists(name):
            raise ValueError('Ctrl {} already exists!'.format(name))

        # create the ctrl node
        _shape = cmds.createNode('mhyController')
        ctrl = cmds.listRelatives(_shape, parent=True)[0]
        ctrl = cls.make_custom_node(ctrl)
        ctrl.name = name
        ctrl.shape.shape_type = shape

        # align ctrl to the target xform and create tag associations
        if xform:
            ctrl.parent_align(xform)
            xform.add_tag('MHYCtrl', ctrl, force=True)
            ctrl.add_tag('MHYCtrlTarget', xform)

        # apply ctrl color
        if not color:
            if name.is_left:
                color = const.COLOR_L
            elif name.is_right:
                color = const.COLOR_R
            else:
                color = const.COLOR_M
        ctrl.shape.shape_color = color

        # apply transforms
        ctrl.shape.local_position = pos
        ctrl.shape.local_rotate = rot
        ctrl.shape.local_scale = scale

        # set rotate order
        if rot_order is None and xform:
            rot_order = xform.rotateOrder.value
        if rot_order is not None:
            ctrl.set_rotate_order(rot_order)

        # create parent groups
        if group_exts:
            _create_ctrl_groups(ctrl, group_exts=group_exts)

        if limb_root:
            ctrl.connect_limb(limb_root)

        # tag for marking menu support
        ctrl.add_marking_menu(const.RIG_MM_NAME)

        return ctrl

    # --- basic properties

    @property
    def limb_root(self):
        """Returns the associated limb root node."""
        for node in cmds.listConnections(
                '{}.message'.format(self),
                source=False, destination=True, plugs=False) or []:
            node = Node(node)
            if node.custom_type_name == 'MHYLimbRoot':
                return node

    @property
    def target(self):
        """Returns the target transform node associated with
        this ctrl at creation time."""
        target = self.get_tag('MHYCtrlTarget')
        if target and cmds.objExists(target):
            return target

    @property
    def shapes(self):
        """Returns the ctrl shape nodes."""
        shapes = self.get_shapes(type_=['mhyController'])
        if not shapes:
            raise RuntimeError(
                'Broken MHYCtrl: {}. No ctrl shape found.'.format(self))
        return shapes

    @property
    def shape(self):
        """Returns the first ctrl shape node."""
        return self.shapes[0]

    # --- group node getters

    def get_group(self, ext):
        """Returns a group node associated with ctrl.

        Args:
            ext (str): The group extension to look for.
        """
        name = NodeName(self)
        k = name.ext.replace('CTRL', '')
        name = NodeName(name, ext=k + ext)

        nodes = cmds.ls(name)
        if len(nodes) == 0:
            return
        elif len(nodes) > 1:
            raise RuntimeError('Duplicated group found: {}'.format(name))
        return Node(name)

    @property
    def plc_node(self):
        """Returns the PLC node, if any."""
        return self.get_group('PLC')

    @property
    def sdk_node(self):
        """Returns the SDK node, if any."""
        return self.get_group('SDK')

    @property
    def pose_node(self):
        """Returns the POSE node, if any."""
        return self.get_group('POSE')

    @property
    def offset_node(self):
        """Returns the OFFSET node, if any."""
        return self.get_group('OFFSET')

    @property
    def inverse_node(self):
        """Returns the INVERSE node, if any."""
        return self.get_group('INVERSE')

    @property
    def null_node(self):
        """Returns the NULL node, if any."""
        return self.get_group('NULL')

    @property
    def wts_transport(self):
        """Returns the wtsTRANSPORT node, if any."""
        return self.get_group('wtsTRANSPORT')

    @property
    def wts_orgin(self):
        """Returns the wtsORGIN node, if any."""
        return self.get_group('wtsOrgin')

    def connect_limb(self, limb_root):
        """Connects this ctrl to a given limb root node.

        Args:
            limb_root (MHYLimbRoot): A limb root node to connect this ctrl to.

        Returns:
            None

        Raises:
            ValueError: If the given limb root is not valid.
            RuntimeError: If this ctrl is already connected to a limb root
                and force is False.
        """
        limb_root = Node(limb_root)
        if limb_root.custom_type_name != 'MHYLimbRoot':
            raise ValueError('{} is not a limb root node!'.format(limb_root))
        limb_root.add_ctrl(self)

    def disconnect_limb(self):
        """Disconnects this ctrl from the current limb, if any."""
        limb_root = self.limb_root
        if limb_root:
            for each in self.get_shapes():
                if each.is_instance:
                    each.delete()

            for each in cmds.listConnections(
                    '{}.message'.format(self),
                    source=True, destination=False, plugs=True) or []:
                node, _ = each.split('.', 1)
                if node == limb_root.name:
                    cmds.removeMultiInstance(each, b=True)

    def get_fkik_switch(self):
        """Returns the FKIK swith attr, if any.

        Returns:
            Attribute or None: The FKIK switch attr.
        """
        for shape in self.get_shapes():
            for attr in shape.list_attr(userDefined=True):
                if attr.name.lower().startswith('ikfk'):
                    return attr
                if attr.name.lower().startswith('fkik'):
                    return attr

    def get_space_switch(self):
        """Returns the space swith attr on this ctrl, if any.

        Returns:
            Attribute: The space switch attr.
        """
        for attr in self.list_attr(userDefined=True):
            if attr.name.startswith(ATTR_SPACE):
                return attr

    def create_space_switch(
            self,
            group_ext='SDK',
            spaces=[],
            attr_node=None,
            default=None,
            local=True,
            world=True,
            mode='pos_rot'):
        """Creates a space switch for his ctrl.

        Space switch is built with a choice node to enable
        bi-directial switches without triggering Maya evaluation cycle.
        i.e. 2 objects can each have a space driven by the other object.

        Args:
            group_ext (str): The extension of the group node to drive.
            spaces (list): A list of spaces. Each item can be one of the two:

                + (space_name, driver_node) pairs.
                + driver_node (the driver node name is used as space name).

            attr_node (Node or str): An object to add the space attribute to.
                If None, add the space attribute on this ctrl.
            default (int or str): The default space index, or space name,
                or driver node.
            local (bool): Add a ctrl local space?
            world (bool): Add a world space?
                This is skipped if the root joint does not exist.
            mode (str): The space switching mode:
                "pos" - Switch position only.
                "rot" - Switch rotation only.
                "pos_rot" - Switch both position and rotation.

        Returns:
            Attribute: The space switch attribute.

        Raises:
            ValueError: If the requested ctrl group is not found.
            ValueError: If any space driver node is not found.
            RuntimeError: If a space swith already exists on this ctrl.
            RuntimeError: If multiple of the same space is requested.
        """
        if self.get_space_switch():
            raise RuntimeError(
                'A space switch already exists on {}'.format(self))

        cname = NodeName(self)
        space_names = []
        drivers = []

        # get the ctrl group offset
        off_node = self.get_group(group_ext)
        if not off_node:
            raise ValueError('{} doesn\'t have a {} group'.format(group_ext))

        # process local and world space
        if local:
            space_names.append('local')
        if world:
            if cmds.objExists(const.ROOT_JOINT):
                space_names.append('world')
                drivers.append(const.ROOT_JOINT)
            else:
                cmds.warning(
                    ('Skipped adding world space... '
                     'World root joint not found: {}').format(const.ROOT_JOINT))

        # process extra requested spaces
        for each in spaces:
            if isinstance(each, (list, tuple)):
                name, node = each
                if not cmds.objExists(node):
                    raise ValueError(
                        'Space driver not found: {}'.format(node))
            elif cmds.objExists(each):
                node = each
                name = str(each).split('|')[-1].split(':')[-1]
            else:
                raise ValueError('Failed to process space: {}'.format(each))

            if name in space_names:
                raise RuntimeError('Multiple "{}" space requested'.format(name))
            space_names.append(name)
            drivers.append(str(node))

        if not space_names:
            cmds.warning('No space to add.')
            return

        # find the default space index
        if default is None:
            default = 0
        elif isinstance(default, int):
            pass
        elif default in space_names:
            default = space_names.index(default)
        elif str(default) in drivers:
            default = space_names.index(str(default))

        # get the space attribute name
        attr = ATTR_SPACE
        if mode == 'pos':
            attr += 'T'
        elif mode == 'rot':
            attr += 'R'

        # get the object to add the space attribute to
        if not attr_node:
            attr_node = self
        else:
            attr_node = Node(attr_node)

        # create the space attr and a choice node for switching
        switch = attr_node.add_attr(
            'enum', name=attr, enumName=':'.join(space_names),
            defaultValue=default, keyable=True)
        ch = Node.create('choice', name=cname.replace_ext('SPACECH'))
        switch >> ch.selector

        # create parent matrix networks
        if local:
            space_names.pop(0)
            if not cmds.objExists(IDEN_MAT_NODE):
                Node.create('fourByFourMatrix', name=IDEN_MAT_NODE)
            m = Node(IDEN_MAT_NODE)
            m.output >> ch.input[0]
            i = 1
        else:
            i = 0

        for driver, name in zip(drivers, space_names):
            drv = Node.create(
                'transform', parent=driver, name='{}__{}'.format(self, name))
            drv.align(off_node)
            mmtx = Node.create(
                'multMatrix', name=cname.replace_ext(name + 'MMTX'))
            drv.worldMatrix[0] >> mmtx.matrixIn[0]
            off_node.parentInverseMatrix >> mmtx.matrixIn[1]
            mmtx.matrixSum >> ch.attr('input[{}]'.format(i))
            i += 1

        # decompse final matrix and pipe into the offset node
        dcm = Node.create('decomposeMatrix', name=cname.replace_ext('PSDCM'))
        ch.output >> dcm.inputMatrix
        off_node.ro >> dcm.inputRotateOrder
        if 'pos' in mode:
            dcm.outputTranslate >> off_node.t
        if 'rot' in mode:
            dcm.outputRotate >> off_node.r

        return switch

    def add_space_switch(self, driver, space=None):
        """Adds a new space into the existing space switch attr.

        Args:
            driver (Node or str): The driver node.
            space (str): The space name. If None, use the driver node name.

        Returns:
            None
        """
        cname = NodeName(self)

        # get the space switch attr
        space_switch = self.get_space_switch()
        if not space_switch:
            raise RuntimeError('{} has no space switch.'.format(self))

        # get the space switch choice node
        ch = cname.replace_ext('SPACECH')
        if not cmds.objExists(ch):
            raise RuntimeError(
                ('Choice node not found, '
                 '{} has a broken space switch.').format(self))
        ch = Node(ch)

        # get the driven offset node
        pat = str(cname).replace('_' + cname.ext, '')
        pat += '_.*'
        off_node = ch.search_node(pat, upstream=False)
        if not off_node:
            raise RuntimeError(
                ('Driven offset node not found, '
                 '{} has a broken space switch.').format(self))

        driver = Node(driver)
        if not space:
            space = driver.name

        # get the updated space list
        spaces = cmds.addAttr(
            space_switch, query=True, enumName=True).split(':')
        if space in spaces:
            raise RuntimeError(
                'Space {} already exists on {}.'.format(space, self))

        # add the new space into the switch attr
        spaces.append(space)
        cmds.addAttr(space_switch, edit=True, enumName=':'.join(spaces))

        drv = Node.create(
            'transform', parent=driver, name='{}__{}'.format(self, space))
        drv.align(off_node)
        mmtx = Node.create(
            'multMatrix', name=cname.replace_ext(space + 'MMTX'))
        drv.worldMatrix[0] >> mmtx.matrixIn[0]
        off_node.parentInverseMatrix >> mmtx.matrixIn[1]
        mmtx.matrixSum >> ch.attr('input[{}]'.format(len(spaces) - 1))

    def create_scale_space_switch(
            self,
            group_ext='OFFSET',
            spaces=['world', 'local'],
            attr_node=None,
            default=None,
            mode='pos_rot'):
        """Creates a scale space switch for the ctrl.

        Default spaces will be local and world. It can take 2-3 spaces.

        Args:
            group_ext (str): The extension of the group node to drive.
            spaces (list): A list of spaces. Each item can be one of the two:

                + (space_name, driver_node) pairs.
                + driver_node (the driver node name is used as space name).

            attr_node (Node or str): An object to add the space attribute to.
                If None, add the space attribute on this ctrl.
            default (int or str): The default space index, or space name,
                or driver node.
            mode (str): The space switching mode:
                "pos" - Switch position only.
                "rot" - Switch rotation only.
                "pos_rot" - Switch both position and rotation.

        Returns:
            Attribute: The space switch attribute.

        Raises:
            ValueError: If the requested ctrl group is not found.
            ValueError: If any space driver node is not found.
            RuntimeError: If a space swith already exists on this ctrl.
            RuntimeError: If multiple of the same space is requested.
        """
        if self.get_space_switch():
            raise RuntimeError(
                'A space switch already exists on {}'.format(self))

        space_names = []
        drivers = []

        # get the ctrl group offset
        off_node = self.get_group(group_ext)
        if not off_node:
            raise ValueError('{} doesn\'t have a {} group'.format(group_ext))

        # process extra requested spaces
        for each in spaces:
            if each == 'world' or each[0] == 'world':
                if cmds.objExists(const.ROOT_JOINT):
                    name = each
                    node = const.ROOT_JOINT
                else:
                    cmds.warning(
                        ('Skipped adding world space... '
                         'World root joint not found: ') + const.ROOT_JOINT)
            elif each == 'local' or each[0] == 'local':
                name = each
                node = off_node.get_parent()
            elif isinstance(each, (list, tuple)):
                name, node = each
                if not cmds.objExists(node):
                    raise ValueError(
                        'Space driver not found: {}'.format(node))
            elif cmds.objExists(each):
                node = each
                name = str(each).split('|')[-1].split(':')[-1]
            else:
                raise ValueError('Failed to process space: {}'.format(each))

            if name in space_names:
                raise RuntimeError('Multiple "{}" space requested'.format(name))
            space_names.append(name)
            drivers.append(str(node))

        if len(space_names) not in [2,3]:
            raise ValueError('Amount of spaces need to be 2 or 3 (include world and local)')

        if not space_names:
            cmds.warning('No space to add.')
            return

        # find the default space index
        if default is None:
            default = 0

        # get the space attribute name
        attr_list = []
        for i in range(1, len(space_names)):
            attr = '_'.join(space_names[i - 1: i + 1])
            if mode == 'pos':
                attr += 'T'
                cns = 'point'
            elif mode == 'rot':
                attr += 'R'
                cns = 'orient'
            else:
                cns = 'parent'
            attr_list.append(attr)

        # get the object to add the space attribute to
        if not attr_node:
            attr_node = self
        else:
            attr_node = Node(attr_node)

        # create the space attr and a choice node for switching
        switch_list = []
        for attr in attr_list:
            switch = attr_node.add_attr(
                'float', name=attr, minValue=0, maxValue=1,
                defaultValue=default, keyable=True)
            switch_list.append(switch)

        # create parent matrix networks
        space_zip = zip(drivers, space_names)
        driver_list = []
        for driver, name in space_zip:
            drv = Node.create(
                'transform', parent=driver, name='{}__{}'.format(self, name))
            drv.align(off_node)
            constraint = off_node.constrain(cns, drv, maintainOffset=True)
            driver_list.append(drv)
        num = len(space_names) - 1
        pre_rmv = None
        for index in range(0, num):
            name = NodeName(attr_node, num=index, ext='SPRMV')
            rmv = Node.create('remapValue', name=name)
            pma = Node.create(
                'plusMinusAverage', name=name.replace_ext('SPPMA'))
            pma.operation.value = 2
            pma.input1D[0].value = 1
            switch_list[index] >> rmv.inputValue
            rmv.outValue >> pma.input1D[1]
            if num == 1:
                rmv.outValue >> constraint.attr(
                    '{}W{}'.format(driver_list[index + 1], index + 1))
                pma.output1D >> constraint.attr(
                    '{}W{}'.format(driver_list[index], index))
            elif pre_rmv:
                mul = Node.create('multiplyDivide', name=name.replace_ext('SPMUL'))
                rmv.outValue >> mul.input2X
                pma.output1D >> mul.input2Y
                pre_rmv.outValue >> mul.input1X
                pre_rmv.outValue >> mul.input1Y
                mul.outputX >> constraint.attr(
                    '{}W{}'.format(driver_list[index + 1], index + 1))
                mul.outputY >> constraint.attr(
                    '{}W{}'.format(driver_list[index], index))
            else:
                pma.output1D >> constraint.attr(
                    '{}W{}'.format(driver_list[index], index))
            pre_rmv = rmv
            '''
            utils.set_driven_keys(
            driver_attr=switch[index],
            driven_attr='{}.{}W{}'.format(constraint, driver_list[index], index),
            value_pairs=((index, 1), (index+1, 0)),
            pre_inf='constant', post_inf='constant')
            utils.set_driven_keys(
            driver_attr=switch,
            driven_attr='{}.{}W{}'.format(constraint, driver_list[index+1], index+1),
            value_pairs=((index, 0), (index+1, 1)),
            pre_inf='constant', post_inf='constant')
            #cmds.setDrivenKeyframe(constraint, attribute='{}W{}'.format(driver_list[index], index), currentDriver=switch, driverValue=index, value=1)
            '''
        return switch_list


class MHYCtrlShape(DagNode):
    """
    A class interfacing anim ctrl shapes used in the MHY rigging system.
    """

    __NODETYPE__ = 'mhyController'

    @property
    def local_position(self):
        """Returns the local postion values."""
        return self.get_attr('localPosition')

    @local_position.setter
    def local_position(self, values):
        """Sets the local postion values."""
        return self.set_attr('localPosition', values)

    @property
    def local_rotate(self):
        """Returns the local rotate values."""
        return self.get_attr('localRotate')

    @local_rotate.setter
    def local_rotate(self, values):
        """Sets the local rotate values."""
        return self.set_attr('localRotate', values)

    @property
    def local_scale(self):
        """Returns the local scale values."""
        return self.get_attr('localScale')

    @local_scale.setter
    def local_scale(self, values):
        """Sets the local scale values."""
        return self.set_attr('localScale', values)

    @property
    def shape_color(self):
        """Returns the ctrl color values."""
        return self.get_attr('color')

    @shape_color.setter
    def shape_color(self, values):
        """Sets the local scale values."""
        return self.set_attr('color', values)

    @property
    def shape_type(self):
        """Returns the ctrl shape type value."""
        types = cmds.attributeQuery(
            'shapeType', node=self.long_name, listEnum=True)[0].split(':')
        return types[self.get_attr('shapeType')]

    @shape_type.setter
    def shape_type(self, typ):
        """Sets the ctrl shape type value.

        Args:
            typ (int or str): A type index or type name string.

        Raises:
            ValueError: If the specifed type string doesn't exist.
        """
        types = cmds.attributeQuery(
            'shapeType', node=self.long_name, listEnum=True)[0].split(':')
        max_id = len(types) - 1

        if not isinstance(typ, int):
            try:
                typ = types.index(typ)
            except BaseException:
                cmds.warning('Shape type not found: {}'.format(typ))
                typ = 0
        elif typ < 0:
            cmds.warning('Shape type index < 0, use 0 instead.')
            typ = 0
        elif typ > max_id:
            cmds.warning(
                'Shape type exceeded max index {}, use {} instead.'.format(
                    max_id, max_id))
            typ = max_id

        self.set_attr('shapeType', typ)

    def get_matrix(
            self, space='object', as_transform=True, as_tuple=True):
        """Returns the shape matrix.

        Args:
            space (str): transform space in which to retrieve the matrix:
                object or world.
            as_transform (bool): If True and as_tuple is False, returns a
                MTransformationMatrix. Otherwise returns MMatrix.
            as_tuple (bool): If True, return a tuple,
                otherwise return MTransformationMatrix.

        Returns: tuple, MMatrix, or MTransformationMatrix
        """
        parent = self.get_parent()
        pos = self.local_position
        pos = OpenMaya.MVector(*pos)
        rot = self.local_rotate
        # The rotation is reversed for some reason...
        rot = [-1 * math.radians(x) for x in rot]
        rot_order = parent.rotateOrder.value
        rot = OpenMaya.MEulerRotation(rot[0], rot[1], rot[2], rot_order)
        scl = self.local_scale

        matrix = parent.get_matrix(
            space='world', as_transform=True, as_tuple=False)
        matrix.addTranslation(pos, OpenMaya.MSpace.kObject)
        matrix.rotateBy(rot, OpenMaya.MSpace.kObject)
        util = OpenMaya.MScriptUtil()
        util.createFromDouble(*scl)
        matrix.setScale(util.asDoublePtr(), OpenMaya.MSpace.kObject)

        if space != 'world':
            pm_matrix = parent.get_matrix(
                space='world', inverse=True, as_transform=False, as_tuple=False)
            matrix = matrix.asMatrix() * pm_matrix
            matrix = OpenMaya.MTransformationMatrix(matrix)

        if not as_tuple:
            if as_transform:
                return matrix
            return matrix.asMatrix()
        return matrix.asMatrix().as_tuple()

    def set_matrix(self, matrix, space='object'):
        """Sets the shape matrix.

        Args:
            matrix(list or MMatrix): A MMatrix or a list of matrix values.
            space (str): transform space in which to retrieve the matrix:
                object or world.

        Returns: None
        """
        if isinstance(matrix, (list, tuple)):
            matrix = OpenMaya.MTransformationMatrix(OpenMaya.MMatrix(matrix))
        elif isinstance(matrix, OpenMaya.MMatrix):
            matrix = OpenMaya.MTransformationMatrix(matrix)
        parent = self.get_parent()

        if space == 'world':
            pm_matrix = parent.get_matrix(
                space='world', inverse=True, as_transform=False, as_tuple=False)
            matrix = matrix.asMatrix() * pm_matrix
            matrix = OpenMaya.MTransformationMatrix(matrix)

        pos = matrix.getTranslation(OpenMaya.MSpace.kWorld)
        self.local_position = pos.as_tuple()

        rot_order = parent.rotateOrder.value
        rot = matrix.eulerRotation()
        rot.reorderIt(rot_order)
        rot = [rot.x, rot.y, rot.z]
        self.local_rotate = [-math.degrees(x) for x in rot]

        util = OpenMaya.MScriptUtil()
        util.createFromDouble(0, 0, 0)
        ptr = util.asDoublePtr()
        matrix.getScale(ptr, OpenMaya.MSpace.kWorld)
        self.local_scale = [
            util.getDoubleArrayItem(ptr, 0),
            util.getDoubleArrayItem(ptr, 1),
            util.getDoubleArrayItem(ptr, 2)]

    def get_translation(self, space='object', as_tuple=True):
        """Retrieve the translation component of this shape
        in linear units.

        Args:
            space (str): transform space in which to retrieve the translation:
                object or world.
            as_tuple (bool): If True, return a tuple, otherwise return MVector.

        Returns:
            tuple or MVector: The translation vector.
        """
        mat = self.get_matrix(space=space, as_transform=True, as_tuple=False)
        vec = mat.getTranslation(OpenMaya.MSpace.kWorld)
        if as_tuple:
            return vec[0], vec[1], vec[2]
        return vec

    def set_translation(self, vector, space='object'):
        """Sets the translation component of this shape.

        Args:
            vector (list or MVector): The translation vector.
            space (str): transform space in which to retrieve the rotation:
                object or world

        Returns: None
        """
        if not isinstance(vector, (list, tuple)):
            vector = (vector[0], vector[1], vector[2])
        vector = OpenMaya.MVector(*vector)

        mat = self.get_matrix(space=space, as_transform=True, as_tuple=False)
        mat.setTranslation(vector, OpenMaya.MSpace.kWorld)

        self.set_matrix(mat, space=space)

    def get_rotation(self, space='object', as_tuple=True):
        """Retrieve the rotation component of this shape.

        Args:
            space (str): transform space in which to retrieve the rotation:
                object or world.
            as_tuple (bool): If True, return a tuple,
                otherwise return MEulerRotation.

        Returns:
            tuple or MEulerRotation: The euler rotation.
        """
        mat = self.get_matrix(space=space, as_transform=True, as_tuple=False)
        rot_order = self.get_parent().rotateOrder.value
        rot = mat.eulerRotation()
        rot.reorderIt(rot_order)
        # again, local rotation is reversed...
        if space == 'object':
            rot *= -1
        if as_tuple:
            return tuple([math.degrees(rot[i]) for i in range(3)])
        return rot

    def set_rotation(self, rot, space='object'):
        """Sets the rotation component of this shape.

        Args:
            rot (list or MEulerRotation): The euler rotation.
            space (str): transform space in which to set the rotation:
                object or world

        Returns: None
        """
        mat = self.get_matrix(space=space, as_transform=True, as_tuple=False)

        rot_order = self.get_parent().rotateOrder.value
        if not isinstance(rot, (list, tuple)):
            rot = (rot[0], rot[1], rot[2])
        rot = [math.radians(x) for x in rot]
        rot = OpenMaya.MEulerRotation(rot[0], rot[1], rot[2], rot_order)
        # again, local rotation is reversed...
        if space == 'object':
            rot *= -1

        mat.rotateTo(rot)
        self.set_matrix(mat, space=space)

    def get_scale(self, space='object', as_tuple=True):
        """Retrieve the scale component of this shape.

        Args:
            space (str): transform space in which to retrieve the scale:
                object or world.
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
        """Sets the rotation component of this shape.

        Args:
            rot (list or MEulerRotation): The euler rotation.
            space (str): transform space in which to set the rotation:
                object or world

        Returns: None
        """
        mat = self.get_matrix(space, as_transform=True, as_tuple=False)

        if not isinstance(scale, (list, tuple)):
            scale = (scale[0], scale[1], scale[2])
        util = OpenMaya.MScriptUtil()
        util.createFromDouble(*scale)
        ptr = util.asDoublePtr()

        mat.setScale(ptr, OpenMaya.MSpace.kWorld)
        self.set_matrix(mat, space=space)
