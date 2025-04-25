import re
from operator import sub

from maya import cmds

from mhy.maya.standard.name import NodeName
from mhy.maya.nodezoo.node import Node
import mhy.maya.nodezoo.utils as nutil
import mhy.maya.maya_math as mmath

import mhy.maya.rig.constants as const


CAT_ATTR = 'categories'
TAG_POSITION = 'closestPointTag'

EXT_TWEAKER_CTRL = 'TKCTRL'
ATTR_TWEAKER_VIS = 'tweaker_ctrl'


def get_ctrl(joint):
    """
    Returns the associated ctrl object.
    MHYCtrl attribute is created during limb building.
    """
    joint = Node(joint)
    if joint.has_attr('MHYCtrl'):
        return joint.get_tag('MHYCtrl')
    else:
        return(None)


def mirror_joint(joint, flip_xy=False, flip_xz=False):
    """Mirrors a joint if it's on the left side.

    Args:
        flip_xy (bool): Mainly for face. If True, flip the orientation.
        flip_xz (bool): If True, flip the orientation.

    Returns:
        Joint: The mirrored joint.
    """
    joint = Node(joint)
    if '_L_' not in joint.name:
        return

    m_jnt = cmds.mirrorJoint(
        joint,
        mirrorYZ=True,
        mirrorBehavior=True,
        searchReplace=('_L_', '_R_'))[0]

    if flip_xy:
        cmds.setAttr(m_jnt + '.rx', -180.0)
        cmds.makeIdentity(m_jnt, apply=True, r=True)
        
    if flip_xz:
        cmds.setAttr(m_jnt + '.rz', 180.0)
        cmds.makeIdentity(m_jnt, apply=True, r=True)

    return Node(m_jnt)


def zero_rotate_channels(joints):
    for jnt in joints:
        parent_jnt = cmds.listRelatives(jnt, p=True)
        if parent_jnt:
            cmds.parent(jnt, w=True)
        
        # get rotate order and set to xyz    
        rot_order = cmds.getAttr('{}.rotateOrder'.format(jnt))
        cmds.setAttr('{}.rotateOrder'.format(jnt), 0)
    
        for ax in 'XYZ':
            rotate = cmds.getAttr('{}.rotate{}'.format(jnt, ax))
            jnt_orient = cmds.getAttr('{}.jointOrient{}'.format(jnt, ax))
            orient_sum = rotate + jnt_orient
            cmds.setAttr('{}.jointOrient{}'.format(jnt, ax), orient_sum)
            cmds.setAttr('{}.rotate{}'.format(jnt, ax), 0.0)
            
        # reset rotate oder back to the original
        cmds.setAttr('{}.rotateOrder'.format(jnt), rot_order)
        
        if parent_jnt:
            cmds.parent(jnt, parent_jnt)


# --- joint category

def get_category(joint):
    """Returns a list of categories associated with a given joint.

    Args:
        joint (str or Node): A joint to work with.

    Returns:
        list: A list of categories.
    """
    joint = Node(joint)
    if joint.has_attr(CAT_ATTR):
        val = joint.get_attr(CAT_ATTR)
        if val:
            return val.split(' ')
    return []


def add_category(joint, category, replace=False):
    """Adds one or more categories onto a given joint.

    Args:
        joint (str or Node): A joint to work with.
        category (str or list): One or more categories to add.
        replace (bool): If True, replace existing categories.

    Returns: None
    """
    joint = Node(joint)
    if not isinstance(category, (list, tuple, set)):
        category = [category]

    # validate category strings
    for i in range(len(category)):
        # Remove all non-word characters
        cat = re.sub(r"[^\w\s]", '', str(category[i]))
        # Replace all runs of whitespace with a underscore
        cat = re.sub(r"\s+", '_', cat)
        if cat != category[i]:
            cmds.warning(
                'Invalid category {}... using {} instead.'.format(
                    category[i], cat))
            category[i] = cat

    if not joint.has_attr(CAT_ATTR):
        joint.add_attr('string', name=CAT_ATTR)

    if not replace:
        category = set(category) | set(get_category(joint))
    category = sorted(list(category))

    attr = joint.attr(CAT_ATTR)
    attr.locked = False
    attr.value = ' '.join(category)
    attr.locked = True


def remove_category(joint, category=None):
    """Removes one or more category from a given joint.

    Args:
        joint (str or Node): A joint to work with.
        category (str or list): One or more categories to remove.

    Returns: None
    """
    joint = Node(joint)
    if not isinstance(category, (list, tuple, set)):
        category = [category]

    if joint.has_attr(CAT_ATTR):
        category = set(get_category(joint)) - set(category)
        if category:
            attr = joint.attr(CAT_ATTR)
            category = sorted(list(category))
            attr.locked = False
            attr.value = ' '.join(category)
            attr.locked = True
        else:
            joint.delete_attr(CAT_ATTR)


def replace_category(joint, old_category, new_category):
    """Replaces one or more categories on a given joint.

    Args:
        joint (str or Node): A joint to work with.
        old_category (str or list): One or more categories to be replaced.
        new_category (str or list): One or more categories to
            replace the old categories.

    Returns:
        None
    """
    remove_category(joint, old_category)
    add_category(joint, new_category)


def has_category(joint, category):
    """Checks if a joint is in one or more categories.

    Args:
        joint (str or Node): A joint to work with.
        category (str or list): One or more categories to check.

    Returns:
        bool
    """
    joint = Node(joint)
    if not joint.has_attr(CAT_ATTR):
        return False

    if not isinstance(category, (list, tuple, set)):
        category = [category]
    if set(get_category(joint)) & set(category):
        return True
    return False


def get_joints_in_category(category, joints=None):
    """Returns a list of joints in the given categories.

    Args:
        category (str or list): One or more categories to work with.
        joints (list): A list of joints to look at.
            If None, look at all joints in the scene.

    Returns:
        list: A list of joints.
    """
    if not isinstance(category, (list, tuple, set)):
        category = [category]
    category = set(category)

    if not joints:
        joints = nutil.ls(type='joint')

    out_joints = []
    for joint in joints:
        if joint.type_name == 'joint' and has_category(joint, category):
            out_joints.append(joint)

    return out_joints


# --- position tag


def get_position_tag(joint, base_geometry):
    """[Transfer joints from one char to another]:
    01. Sets position tags for a list of joints.

    Create position dag to facial transform using 'closestPointOnMesh'
    Dag attributes include:

    + vtx index number
    + offset from the dagged vertex
    + UV position dag (option to snap to world position or uv position)

    Args:
        joint (str or Node): A joint to work with.
        base_geometry (TODO): TODO

    Returns:
        TODO: Change from adding attrs on joint to writing out data to joints.json
    """
    joint = Node(joint)
    cpom = Node.create('closestPointOnMesh')
    shape = Node(base_geometry).get_shapes()[0]
    shape.worldMesh >> cpom.inMesh

    attrs = (TAG_POSITION,
             'offsetX', 'offsetY', 'offsetZ',
             'textureU', 'textureV')

    '''
    # add position and offset attributes
    if not joint.has_attr(TAG_POSITION):
        joint.add_attr('string', name=TAG_POSITION)
        for attr in attrs:
            try:
                joint.add_attr('double', name=attr)
            except BaseException:
                continue
    else:
        for attr in attrs:
            joint.attr(attr).locked = False
    '''
    
    # get closest point on dag geo
    cpom.inPosition.value = joint.get_translation(space='world')
    cpoint = cpom.closestVertexIndex.value
    p_tag = 'vtx[{}]'.format(str(cpoint))

    # get offset values
    offset = get_position_offset(joint, '{}.{}'.format(base_geometry, p_tag) )

    # get uv point
    u = cpom.parameterU.value
    v = cpom.parameterV.value

    '''
    # set attributes
    for attr, val in zip(
            attrs, (p_tag, offset[0], offset[1], offset[2], u, v)):
        attr = joint.attr(attr)
        attr.value = val
        attr.locked = True
    ''' 
    
    #
    out_data={}
    for attr, val in zip(
            attrs, (p_tag, offset[0], offset[1], offset[2], u, v)):
        out_data[attr] = val
    
    # cleanup
    cpom.delete()
    
    return out_data


def snap_to_position_tag(joint, geometry, offset=True):
    """
    [Transfer joints from one char to another]:
    04: Snap to Dagged World Position

    Move joint to its position dag point with or without offset
    * This step cannot be done after jaw deformable mesh is added

    Args:
        joint (str or Node): A joint to work with.
        offset (bool): True = add offset, False = no offset
        TODO

    Returns:
        TODO
    """
    joint = Node(joint)
    if not joint.has_attr(TAG_POSITION):
        cmds.warning('{} does not have position tag.'.format(joint))
        return

    parent = joint.get_parent()
    joint.set_parent(None)

    p_index = joint.attr(TAG_POSITION).value
    vert = '{}.{}'.format(geometry, p_index)
    pt_pos = cmds.xform(vert, q=True, ws=True, t=True)

    if not offset:
        cmds.joint(
            joint, edit=True, relative=False,
            position=pt_pos, component=True)
    else:
        pos = []
        for i, ch in enumerate('XYZ'):
            val = joint.attr('offset' + ch).value + pt_pos[i]
            pos.append(val)

        cmds.joint(
            joint, edit=True, relative=False,
            position=pos, component=True)

    if parent:
        joint.set_parent(parent)


def get_position_offset(joint, position_tag):
    """[Transfer joints from one char to another]:
    02- Get Position Offset
    Get the distance btwn position dag point and facial transform

    TODO
    """
    pt_pos = cmds.xform(
        position_tag, query=True, worldSpace=True, translation=True)
    jnt_pos = cmds.xform(joint, query=True, worldSpace=True, translation=True)
    return tuple(map(sub, jnt_pos, pt_pos))


# --- misc


def update_label(joint, type_=None, draw=False):
    """Sets the joint label based on the joint name and embeded data.

    Args:
        type_ (str): The type name.
            If None, try get the type name from embeded 'type' attr.
        draw (bool): If True, turn on label drawing.

    Returns: None
    """
    joint = Node(joint)
    types = cmds.attributeQuery(
        'type', node=joint.long_name, listEnum=True)[0].split(':')
    type_dict = {}
    for i, attr in enumerate(types):
        type_dict[attr] = i
    name = NodeName(joint.name)

    # set type
    type_id = type_dict.get(type_)
    if type_id is None:
        type_ = 'Other'
        type_id = type_dict['Other']

    joint.set_attr('type', type_id)
    if type_ == 'Other':
        type_ = name.part
        desc = name.desc
        if desc:
            type_ += '_{}'.format(desc)
        joint.set_attr('otherType', type_)

    # set side
    if name.is_middle:
        side = 0
    elif name.is_left:
        side = 1
    elif name.is_right:
        side = 2
    else:
        side = 3
    joint.set_attr('side', side)

    # set drawing state
    joint.set_attr('drawLabel', draw)


def add_twist_joints(start_joint, end_joint, amount=1):
    """Adds a list of twist joints between the start joint and the end joint.

    Args:
        start_joint (str or Node): Twist start joint.
        end_joint (str or Node): Twist end joint.
        amount (int): Number of twist joints to build.

    Returns:
        list: A list of twist joints created.
    """
    start_joint = Node(start_joint)
    end_joint = Node(end_joint)
    dist = mmath.distance(start_joint, end_joint) / amount
    if start_joint.long_axis.startswith('-'):
        dist *= -1
    base_name = NodeName(start_joint)

    twist_joints = []
    for i in range(amount):
        name = NodeName(base_name, desc=base_name.desc + 'Twist', num=i)
        if cmds.objExists(name):
            raise RuntimeError(
                'twistJoint:{} is already existed'.format(name))
        twist_jnt = start_joint.duplicate(
            name=name, inputConnections=False, parentOnly=True)[0]
        twist_jnt.unlock()
        twist_jnt.set_parent(start_joint)
        twist_jnt.tx.value = dist * i
        twist_joints.append(twist_jnt)

    return twist_joints


class JointChain(object):
    """
    A class interfacing joint chains.
    """

    def __init__(self, start=None, end=None):
        """Initializes a joint chaing object.

        Args:
            start (str, Node): The start joint.
            end (str, Node or None): The end joint (Optional).
                If None, use the entire joint hierarchy under the start joint.
        """
        self.__start = Node(start)
        self.__end = Node(end) if end else None

    def __str__(self):
        return str(self.joints)

    def __len__(self):
        return len(self.joints)

    def __getitem__(self, key):
        return self.joints[key]

    def __setitem__(self, i, joint):
        self.joints[i] = joint

    def __iter__(self):
        return iter(self.joints)

    def __contains__(self, joint):
        return joint in self.joints

    @property
    def joints(self):
        """Returns the joint chain."""
        return self.__start.get_hierarchy(skip_self=False, end=self.__end)

    @property
    def chain_length(self):
        """Returnt the length of this joint chain."""
        return self.__start.get_chain_length(end=self.__end)

    @property
    def long_axis(self):
        """Returns the long axis of this chain name as 'X', 'Y', or 'Z'.
        Returns None if axis are mixed.
        """
        long_axis = []
        for joint in self.joints:
            if joint != self.__end:
                long_axis.append(joint.long_axis)
        result = all(ax == long_axis[0] for ax in long_axis)

        if result:
            return long_axis[0]

    @property
    def up_axis(self):
        """
        Returns the up axis of this chain as 'X', 'Y', or 'Z'.
        The up axis is the axis parallel to the chain's normal.

        The first, middle, and last joint are used to generate a triangle for
        normal calculation. On chains with greater than 3 joints this value
        may not be useful.
        """
        # TODO
        pass

    @property
    def cross_axis(self):
        """
        Returns the cross axis of this chain as 'X', 'Y', or 'Z'.
        The cross axis is the axis perpendicular to the chain's normal. It lies
        on the plane of the chain.

        The first, middle, and last joint are used to generate a triangle for
        cross calculation. On chains with greater than 3 joints this value may
        not be useful.
        """
        # TODO
        pass

    def get_pole_vector(self, distance=None):
        """Returns the world space position of the pole vector for
        this joint chain.

        The function will use the first, middle, and last joints to determine
        normal and tangent to get the aim.

        Args:
            distance (float) : The distance multiplier for the aim.
                If None, use half of the distance from start joint to end joint.

        Returns:
            tuple: The pole vector position.

        Raises:
            RuntimeError: If the iber of joints is less than 3.
        """
        joints = self.joints
        if len(joints) < 3:
            raise RuntimeError(
                ('Need at least 3 joints to calculate pole vector. '
                 'Joint chain: {}').format(joints))

        # get start, mid, and end positions
        start_pnt = joints[0].get_translation(space='world', as_tuple=False)
        end_pnt = joints[-1].get_translation(space='world', as_tuple=False)
        mid_pnt = mmath.get_position_center(joints[1:-1], as_tuple=False)

        # get 3 distance value among three joints
        start_mid_dist = mmath.distance(start_pnt, mid_pnt)
        mid_end_dist = mmath.distance(mid_pnt, end_pnt)
        if not distance:
            distance = (mmath.distance(start_pnt, end_pnt) / 2.0)

        factor = start_mid_dist / (start_mid_dist + mid_end_dist)
        p_mid_point = mmath.get_fractional_position(
            start_pnt, end_pnt, fraction=factor, as_tuple=False)
        v_vector = (mid_pnt - p_mid_point).normal()
        v_vector = v_vector * distance + mid_pnt
        return v_vector.x, v_vector.y, v_vector.z

    def set_rotate_order(self, order):
        """Sets the rotate order for this chain."""
        for joint in self.joints:
            joint.set_rotate_order(order)


# --- bind skeleton


def get_bind_parent(rig_joint):
    """Returns the bind parent of a given rig joint.

    Args:
        rig_joint (Joint or str): A rig joint to work with.

    Returns:
        Joint or None: The bind parent joint.
    """
    rig_joint = Node(rig_joint)
    if rig_joint.has_attr(const.ATTR_BIND_PARENT):
        parent = rig_joint.get_tag(const.ATTR_BIND_PARENT)
        if parent:
            return parent


def get_closest_bind_parent(rig_joint):
    """Given a rig joint, return it's closest exportable parent.

    Args:
        rig_joint (Joint or str): A rig joint to work with.

    Returns:
        Joint or None: The closest bind parent joint.
    """
    rig_joint = Node(rig_joint)
    parent = rig_joint
    part = NodeName(parent).part

    while parent and NodeName(parent).part == part:
        parent = parent.get_parent()
        if parent and is_bind_joint(parent):
            return parent


def is_bind_joint(joint):
    """Checks if a joint is a bind joint.

    Returns:
        bool
    """
    return Node(joint).has_attr(const.ATTR_BIND_PARENT)


def get_bind_joint(rig_joint, name_rule=None):
    """Returns the bind joint associated with a given rig joint.

    Args:
        rig_joint (Joint or str): A rig joint to work with.
        name_rule (str): A string defining rig joint to bind joint
            naming convention. e.g. "{part}_{desc}_{num}_{side}"

                + {part}: Use all lower case
                + {Part}: Use caplitalized.
                + {PART}: Use all upper case.

            If None, return the default conversion result.

    Returns:
        Joint or None: The bind joint.
    """
    rig_joint = Node(rig_joint)
    bind_joint = None
    if rig_joint.has_attr(const.ATTR_BIND_JOINT):
        bind_joint = rig_joint.get_tag(const.ATTR_BIND_JOINT)
    if not bind_joint:
        bind_joint = get_bind_joint_name(rig_joint, name_rule=name_rule)
        if cmds.objExists(bind_joint):
            bind_joint = Node(bind_joint)
        else:
            bind_joint = None
    return bind_joint


def set_bind_joint(rig_joint, bind_joint):
    """Explicitly associates a bind joint with a given rig joint.

    Args:
        rig_joint (Joint or str): A rig joint to work with.
        rig_joint (Joint or str): A bind joint to work with.

    Returns:
        None
    """
    Node(rig_joint).add_tag(const.ATTR_BIND_JOINT, bind_joint, force=True)


def add_tweaker_ctrl(bind_joint):
    """
    Adds a tweaker ctrl to a given bind joint.
    """
    limb_root = NodeName(bind_joint, num=None, desc='ROOT', ext='LIMB')
    ctrl_root = NodeName(bind_joint, num=None, desc='ROOT', ext='CONTROL')
    if not cmds.objExists(limb_root) or not cmds.objExists(ctrl_root):
        cmds.warning('Ctrl root not found: {}'.format(ctrl_root))
        return

    # create the tweaker group node and vis attr
    group = NodeName(ctrl_root, ext='TWEAKER')
    if not cmds.objExists(group):
        group = Node.create('transform', name=group, parent=ctrl_root)
        if cmds.objExists(const.RIG_ROOT):
            rig_root = Node(const.RIG_ROOT)
            if not rig_root.has_attr(ATTR_TWEAKER_VIS):
                vis_attr = rig_root.add_attr(
                    'bool', name=ATTR_TWEAKER_VIS, defaultValue=False)
                vis_attr.channelBox = True
            else:
                vis_attr = rig_root.attr(ATTR_TWEAKER_VIS)
            vis_attr >> group.v
    else:
        group = Node(group)

    name = NodeName(bind_joint, ext=EXT_TWEAKER_CTRL)
    # skip if a tweaker ctrl alreay exists
    if cmds.objExists(name):
        return

    # only constraint joints are allowed
    constraints = bind_joint.get_children(type_='constraint')
    if not constraints:
        cmds.warning(
            ('Can\'t create tweaker ctrl for '
                'non-constraint joint {}').format(bind_joint))
        return

    # create the tweaker ctrl
    tk_ctrl = Node.create(
        'MHYCtrl',
        shape='sphere',
        color=(1, 1, 1),
        scale=(.5, .5, .5),
        name=name,
        group_exts=['PLC', 'OFFSET'],
        limb_root=limb_root)
    tk_ctrl.plc_node.set_parent(group)
    tk_ctrl.plc_node.align(bind_joint.get_parent())
    off_node = tk_ctrl.offset_node
    off_node.rotateOrder.value = bind_joint.rotateOrder.value
    off_node.align(bind_joint)

    # move constraints and connections to the offset node
    bind_joint.move_connections(off_node, connected_nodes=constraints)
    cmds.parent(constraints, off_node)

    # connect tweaker ctrl to joint
    bind_joint.constrain('parent', tk_ctrl, maintainOffset=True)
    # bind_joint.constrain('scale', tk_ctrl, maintainOffset=True)
    tk_ctrl.s >> bind_joint.s

    # clean up
    tk_ctrl.lock('v')


def get_bind_joint_name(rig_joint, name_rule=None):
    """Returns a proper bind joint name from a given rig joint and
    name convertion rule.

    Args:
        rig_joint (Joint or str): A rig joint to work with.
        name_rule (str): A string defining rig joint to bind joint
            naming convention. e.g. "{part}_{desc}_{num}_{side}"

                + {part}: Use all lower case
                + {Part}: Use caplitalized.
                + {PART}: Use all upper case.

            If None, return the default conversion result.

    Returns:
        str: The bind joint name.
    """
    name = NodeName(rig_joint)
    if not name_rule:
        return name.replace_ext(const.EXT_BIND_JOINT)

    part = name.part
    new_name = name_rule.replace('{part}', part.lower())
    new_name = new_name.replace('{PART}', part.upper())
    new_name = new_name.replace('{Part}', part.lower().capitalize())

    desc = name.desc
    if not desc:
        desc = ''
    new_name = new_name.replace('{desc}', desc.lower())
    new_name = new_name.replace('{Desc}', desc.upper())
    new_name = new_name.replace('{DESC}', desc.lower().capitalize())

    num = name.num
    if num is None:
        num = ''
    else:
        num = '{:02d}'.format(num)
    new_name = new_name.replace('{num}', num.lower())
    new_name = new_name.replace('{Num}', num.upper())
    new_name = new_name.replace('{NUM}', num.lower().capitalize())

    side = name.side
    if not side:
        side = ''
    new_name = new_name.replace('{side}', side.lower())
    new_name = new_name.replace('{Side}', side.upper())
    new_name = new_name.replace('{SIDE}', side.lower().capitalize())

    ext = name.ext
    new_name = new_name.replace('{ext}', ext.lower())
    new_name = new_name.replace('{Ext}', ext.upper())
    new_name = new_name.replace('{EXT}', ext.lower().capitalize())

    for i in range(5, 0, -1):
        new_name = new_name.replace('_' * i, '_')
    return new_name


def create_bind_skeleton(
        rig_joint=None, attach=False, tweaker_ctrls=False,
        name_dict=None, name_rule=None):
    """Builds a bind skeleton from all the tagged
    rig joints in the scene.

    Args:
        rig_joint (Joint or str): If not None, **ONLY** operate
            on this rig joint.
        attach (bool): If True, attach each bind joint to the
            associated rig joint.
        tweaker_ctrls (bool): If True, create a tweaker ctrl for
            each bind joint.
            This arg is skipped if attach is False.
        name_dict (dict): A dict converting rig joint names to
            explicit bind joint names.
        name_rule (str): A string defining rig joint to bind joint
            naming convention. e.g. "{part}_{desc}_{num}_{side}"

                + {part}: Use all lower case
                + {Part}: Use caplitalized.
                + {PART}: Use all upper case.

            If None, return the default conversion result.

    Returns:
        None
    """
    if not rig_joint:
        rig_joints = cmds.ls('*.{}'.format(
            const.ATTR_BIND_PARENT), objectsOnly=True)
    else:
        rig_joints = [rig_joint]
    for rig_joint in rig_joints:
        bind_joint = get_bind_joint(rig_joint, name_rule=name_rule)
        if bind_joint:
            continue
        if name_dict:
            bind_joint = name_dict.get(str(rig_joint))
        if not bind_joint:
            bind_joint = get_bind_joint_name(rig_joint, name_rule=name_rule)

        rig_joint = Node(rig_joint)
        rig_parent = get_bind_parent(rig_joint)
        bind_parent = None
        if rig_parent:
            bind_parent = get_bind_joint(rig_parent, name_rule=name_rule)
            if not bind_parent:
                create_bind_skeleton(
                    rig_joint=rig_parent,
                    attach=attach, tweaker_ctrls=tweaker_ctrls, name_rule=name_rule)
                bind_parent = get_bind_joint(rig_parent, name_rule=name_rule)
        bind_joint = Node.create(
            'joint', name=bind_joint, clear_selection=True)
        bind_joint.rotateOrder.value = rig_joint.rotateOrder.value
        mtx = rig_joint.get_matrix(space='world')
        bind_joint.set_matrix(mtx, space='world')

        if not bind_parent:
            bind_parent = const.BIND_SKEL_ROOT
            if not cmds.objExists(bind_parent):
                root = Node.create('transform', name=const.BIND_SKEL_ROOT)
                if cmds.objExists(const.RIG_ROOT):
                    root.set_parent(const.RIG_ROOT)

        bind_joint.set_parent(bind_parent)
        bind_joint.make_identity(apply=True, rotate=True, scale=True)

        if attach:
            bind_joint.constrain('parent', rig_joint, maintainOffset=False)
            bind_joint.constrain('scale', rig_joint, maintainOffset=False)
            if tweaker_ctrls:
                add_tweaker_ctrl(bind_joint)
