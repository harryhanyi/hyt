import os
import abc
from six import string_types
from collections import OrderedDict

import maya.cmds as cmds
from mhy.protostar.core.action import MayaAction, custom_exec_method
import mhy.protostar.core.parameter as pa
import mhy.protostar.core.parameter_base as pb
import mhy.protostar.core.exception as exp

from mhy.maya.nodezoo.node import Node
from mhy.maya.standard.name import NodeName
import mhy.maya.maya_math as mmath

import mhy.maya.rig.constants as const
import mhy.maya.rig.marker_system as ms
import mhy.maya.rig.joint_utils as jutil
import mhy.maya.rig.utils as util


LIMB_ROOT_COLOR = (1, 1, 1)
CTRL_ROOT_COLOR = (.8, .5, .15)
CTRL_LEAF_COLOR = (.25, .75, .35)


class BaseLimb(MayaAction):
    """Base abstract limb class for all rig limbs to inherit.

    All limbs will include these nodes:

        + Limb root:  the top group node, also acts as the default plug node.
        + Worldspace Root: for objects not inheriting transform,
          e.g. defomring geometries.
        + Limb ctrl root: where all ctrls within the limb will be under.
        + Limb ctrl leaf: for other limbs to connect to.
    """

    # the limb type string
    _LIMB_TYPE = None

    # the default side token
    _DEFAULT_SIDE = NodeName.SIDE_M

    # if True, build a worldspace root. otherwise skip it.
    _REQUIRE_WS_ROOT = True

    # name of the vis attribute to toggle this limb
    _CTRL_VIS_ATTR = 'body_ctrl'

    # input skeleton type. must be one of the types defined
    # in _INPUT_SKEL_TYPES.
    # only used for resolving parameter "input_skeleton".
    _INPUT_SKEL_TYPE = const.InputSkelType.single_chain

    # if True, the root bind joint(s) of this limb will replace
    # its parent limb's bind socket joint at connection time.
    #
    # otherwise the root bind joint(s) will be connected directly
    # to the parent limb's bind sokect joint.
    _REPLACE_BIND_SOCKET = False

    _TAGS = ['rig limb']
    _UI_COLOR = (37, 112, 143)
    _UI_ICON = 'base_limb'

    # --- input parameters

    @pa.str_param()
    def part(self):
        """The limb part name. Each limb must have an unique part name."""

    @pa.enum_param(items=('L', 'R', 'M'))
    def side(self):
        """The side token."""

    @pa.bool_param(default=False)
    def mirror(self):
        """If True, also create a mirrored version of this limb."""

    @pa.message_param()
    def parent_limb(self):
        """A parent limb action to connect this limb to."""

    @pa.list_param(item_type='str')
    def input_skeleton(self):
        """If not empty, skip marker system and use an existing rig skeleton
        resolved from the value of this parameter.

        The value should be one of the following format:

            * [start_joint]:

              resolve to a single-joint skeleton.
              use this format if the limb requires a single joint.

            * [start_joint, end_joint]

              resolve to a single-chain skeleton.
              use this format if the limb requires a single chain.
              (this is the most common senario).

            * [[start_joint1, end_joint1], [start_joint2, end_joint2], ...]

              resolve to a multi-chain skeleton.
              use this format if the limb requires multiple chains.
        """

    @pa.str_param()
    def parent_joint(self):
        """If not empty, skip marker system and directly use this joint
        as the parent socket joint. Used together with `input_skeleton`.
        """

    # --- output parameters

    @pa.pyobject_param(output=True)
    def limb_root(self):
        """The root transform node of this limb.
        Avaiable after start() is executed.

        :type: MHYLimbRoot
        """

    @pa.pyobject_param(output=True)
    def mirrored_limb(self):
        """The mirrored limb action object, if parameter
        "mirror" is set to True. Otherwise returns None.

        :type: BaseLimb
        """

    # --- end of parameter definition

    def __init__(self, *args, **kwargs):
        """Initializes a new limb object."""
        super(BaseLimb, self).__init__(*args, **kwargs)
        self._reset_private_vars()
        self.__parent_limb = None
        self.__sources_limb = None
        self.__rig_skel_matrices = {}
        self.part.default = self._LIMB_TYPE
        self.side.default = self._DEFAULT_SIDE
        if self._INPUT_SKEL_TYPE not in const.InputSkelType.items():
            raise exp.ActionError(
                'Invalid input skeleton type: {}'.format(self._INPUT_SKEL_TYPE))

    def _reset_private_vars(self):
        """Resets private variables."""
        self.__rig_skeleton = []
        self.__root_bind_joints = []

        self.__constraints = []
        self.__ws_root = None
        self.__ctrl_root = None
        self.__ctrl_leaf = None
        self.__ctrl_leaf_parent = None
        self.__plugs = []

        self.__mirrored_limb = None

    # --- basic properties

    @property
    def limb_type(self):
        """The limb type string."""
        if self._LIMB_TYPE:
            return self._LIMB_TYPE
        return self.class_name

    @property
    def ws_root(self):
        """The worldspace root node.
        Avaiable after start() is executed.

        :type: Transform
        """
        return self.__ws_root

    @property
    def ctrl_root(self):
        """The ctrl root node.
        Avaiable after start() is executed.

        :type: Transform
        """
        return self.__ctrl_root

    @property
    def ctrl_leaf(self):
        """The ctrl leaf node."""
        return self.__ctrl_leaf

    @property
    def ctrl_leaf_parent(self):
        """The ctrl leaf parent of this limb.
        Ctrl leaf parent is the last built ctrl unless explicitly
        set by the user.

        :type: Transform
        :setter: Sets the ctrl leaf parent.
        """
        if not self.__ctrl_leaf_parent:
            ctrls = self.get_ctrls()
            if ctrls:
                return ctrls[-1]
        return self.__ctrl_leaf_parent

    @ctrl_leaf_parent.setter
    def ctrl_leaf_parent(self, node):
        if not cmds.objExists(node):
            raise exp.ActionError('Leaf parent node not found: {}'.format(node))
        self.__ctrl_leaf_parent = Node(node)

    @property
    def _mirrored_limb(self):
        """The mirrored limb.
        Avaiable after self.mirror_limb() is called.

        :type: BaseLimb or None
        :setter: Sets the mirrored limb.
        """
        return self.__mirrored_limb

    @_mirrored_limb.setter
    def _mirrored_limb(self, limb):
        self.__mirrored_limb = limb

    @property
    def _source_limb(self):
        """The source limb that this limb is mirrored from.
        Avaiable after only on the mirrored limbs.

        :type: BaseLimb or None
        :setter: Sets the source limb.
        """
        return self.__sources_limb

    @_source_limb.setter
    def _source_limb(self, limb):
        self.__sources_limb = limb

    def get_ctrls(self):
        """Returns the ctrls built in this limb at the moment of query.

        Returns:
            list: A list of MHYCtrl objects.
        """
        return self.limb_root.value.get_ctrls()

    # --- marker system

    def get_parent_limb(self):
        """Returns the parent limb action connected to the
        "parent_limb" parameter.

        Returns:
            BaseLimb or None: The parent limb action.
        """
        if self.__parent_limb:
            return self.__parent_limb
        return self.parent_limb.value

    def set_parent_limb(self, limb):
        """Sets the parent limb action by creating connection:
            parent_limb.message >> self.parent_limb
        """
        if not limb:
            self.parent_limb.clear_script()
        else:
            if isinstance(limb, BaseLimb):
                limb.message >> self.parent_limb
            elif isinstance(limb, pb.base_parameter):
                limb >> self.parent_limb
            else:
                raise ValueError(
                    '{} is not a limb action or parameter.'.format(limb))

    def _override_parent_limb(self, limb):
        """Overrides the parent limb.
        Used **INTERNALLY** for mirroing."""
        if not isinstance(limb, BaseLimb):
            raise exp.ActionError('{} is not a limb object.'.format(limb))
        self.__parent_limb = limb

    @property
    def marker_system(self):
        """The associated marker system object in the scene,
        or None if not found.

        :type: MarkerSystem
        """
        part = self.part.value
        side = self.side.enum_value
        ms_name = ms.MarkerSystem.marker_root_name(part, side)
        if cmds.objExists(ms_name):
            return ms.MarkerSystem(ms_name)

    @abc.abstractmethod
    def marker_data(self):
        """Returns the marker data dict, which defines the
        marker system for this limb.

        See `MarkerSystem
        <../autoapi/mhy.maya.rig.marker_system.MarkerSystem.html>`_
        for details on the data format."""

    @custom_exec_method
    def build_marker(self):
        """Builds the marker system for this limb. Also builds
        the mirrored marker system if the "mirror" parameter is True.

        Returns:
            MarkerSystem or None: The marker system object,
            or None if this limb's marker data is empty.
        """
        # get developer-defined marker data
        marker_data = self.marker_data()
        if not marker_data:
            return

        # create the marker system
        part = self.part.value
        side = self.side.enum_value
        parent = self.get_parent_limb()
        marker_sys = ms.MarkerSystem.create(
            part, side, marker_data=marker_data, force=False)
        if parent:
            self.connect_marker_system(parent)

        # create the mirrored marker system
        if marker_sys:
            if self.mirror.value:
                self.mirror_limb(exec_name='build_marker')
                marker_sys.mirror()

        return marker_sys

    def connect_marker_system(self, parent_limb):
        """Connects this marker system to the parent marker system.
        The default behavior is to connect to the parent limb's
        first marker chain's end marker (0, -1).
        """
        parent_ms = parent_limb.marker_system
        if parent_ms:
            pmarker = parent_ms.get_marker(0, -1)
            self.marker_system.set_parent_marker(pmarker)

    def get_marker(self, chain_id, marker_id):
        """Returns the marker node at the given indices.

        Args:
            chain_id (int): The marker chain id.
            marker_id (int): The marker id.

        Returns:
            MHYMarker: The marker node.
        """
        marker_sys = self.marker_system
        if marker_sys:
            return marker_sys.get_marker(chain_id, marker_id)

    # --- rig and bind skeleton

    def build_marker_skeleton(self):
        """Builds the skeleton from the associated marker system,
        then update self.rig_skeleton.

        The structure of self.rig_skeleton follows the marker data
        constructed by self.marker_data(). This allows the
        developer to easily locate joints when implementing self.run().

        No skeleton will be built if self.marker_data() returns None.

        Raises:
            ActionError: If the associated marker system does not exist.
        """
        # get default marker data
        marker_data = self.marker_data()
        if not marker_data:
            return

        # build skeleton from the marker system
        # find the associated marker system
        marker_sys = self.marker_system
        if not marker_sys:
            raise exp.ActionError('{}: Marker system not found!'.format(self))

        # and update self.__rig_skeleton
        if cmds.objExists(const.ROOT_JOINT):
            parent = const.ROOT_JOINT
        else:
            if not cmds.objExists(const.RIG_SKEL_ROOT):
                Node.create('transform', name=const.RIG_SKEL_ROOT)
            parent = const.RIG_SKEL_ROOT
        self.__rig_skeleton = marker_sys.build_skeleton(parent=parent)

    def resolve_input_skeleton(self):
        """This is the method that resolves "input_skeleton" parameter,
        if not empty. (used by the user to pass in a pre-built skeleton).

        If "input_skeleton" is not empty, marker system will be skipped and
        the limb execution will directly use the joints provided by the user.
        """
        val = self.input_skeleton.value
        if not val:
            if not self.marker_data():
                raise exp.ParameterError('Input skeleton is empty!')
            return

        try:
            if self._INPUT_SKEL_TYPE == const.InputSkelType.single_joint:
                self.__rig_skeleton = [[Node(val[0])]]
            elif self._INPUT_SKEL_TYPE == const.InputSkelType.single_chain:
                if len(val) == 1:
                    val = (val[0], val[0])
                self.__rig_skeleton = [Node(val[0]).get_chain(val[1])]
            else:
                self.__rig_skeleton = []
                for chain in val:
                    if len(chain) == 1:
                        self.__rig_skeleton.append([Node(chain[0])])
                    else:
                        self.__rig_skeleton.append(val[0].get_chain(val[1]))
        except BaseException as e:
            print(e)
            raise exp.ParameterError(
                ('Failed resolving parameter "input_skeleton"...'
                 'the raw value is {}. '
                 '{} requires a {} skeleton').format(
                     val, self.type_name, self._INPUT_SKEL_TYPE))

    @property
    def rig_skeleton(self):
        """Returns the rig skeleton either constructed by
        self.build_marker_skeleton() or established by
        self.resolve_input_skeleton().

        If both are present, parameter "input_skeleton" will override
        the marker system.

        The format of the return value is a list of joint lists. Each sub-list
        represents a chain of joints.

        If marker system is used, the structure of self.rig_skeleton follows the
        marker data constructed by self.marker_data(). This allows developers
        to easily locate the joints they need when implementing self.run().

        If input_skeleton is used, self.resolve_input_skeleton() must be
        implemented properly to meet all usage expectations.
        """
        return self.__rig_skeleton

    def _set_rig_skeleton(self, skel):
        """Sets the rig skeleton."""
        if not isinstance(skel, (list, tuple)):
            self.__rig_skeleton = [skel]
        else:
            self.__rig_skeleton = skel

    def __cache_rig_skel_matrices(self):
        """Caches the matrix of each rig joint."""
        self.__rig_skel_matrices = {}
        for chain in self.__rig_skeleton:
            for joint in chain:
                self.__rig_skel_matrices[joint] = joint.get_matrix(
                    space='world', as_tuple=False)

    def __validate_rig_skel(self):
        """Checks if the rig skeleton is changed by comparing the current
        rig skeleton with the cached matrices."""
        missing_joints = []
        changed_joints = []
        for joint, mat in self.__rig_skel_matrices.items():
            if not cmds.objExists(joint):
                missing_joints.append(joint.name)
            else:
                new_mat = joint.get_matrix(space='world', as_tuple=False)
                if not new_mat.isEquivalent(mat, 0.001):
                    changed_joints.append(joint.name)

        if missing_joints or changed_joints:
            msg = 'Rig joints changed by ctrl rig build...'
            if missing_joints:
                msg += '\nRemoved joints: {}'.format(', '.join(missing_joints))
            if changed_joints:
                msg += '\nChanged joints: {}'.format(', '.join(changed_joints))
            raise exp.ActionError(msg)

    def tag_bind_joint(self, rig_joint, parent=None):
        """Tags a rig joint as a bind joint of this limb.

        Args:
            rig_joint (Joint or str): A rig joint to tag.
            parent (Joint or str): The parent rig joint.

        Returns:
            None
        """
        if parent and str(rig_joint) == str(parent):
            raise ValueError('Cannot set self as bind parent: {}'.format(rig_joint))
        rig_joint = Node(rig_joint)
        rig_joint.add_tag(
            const.ATTR_BIND_PARENT, parent, force=True)
        if not parent:
            self.__root_bind_joints.append(rig_joint)

    def untag_bind_joint(self, rig_joint):
        """Untags a rig joint as a bind joint of this limb.

        Args:
            rig_joint (Joint or str): A rig joint to untag.

        Returns:
            None
        """
        rig_joint = Node(rig_joint)
        if rig_joint.has_attr(const.ATTR_BIND_PARENT):
            rig_joint.delete_attr(const.ATTR_BIND_PARENT)
        if rig_joint in self.__root_bind_joints:
            self.__root_bind_joints.remove(rig_joint)

    def tag_bind_hierarchy(self, root_joint):
        """Tags all joints under a given root joint as bind joints.

        Args:
            root_joint (Joint or str): A root joint to work with.

        Returns:
            None
        """
        root_joint = Node(root_joint)
        for joint in root_joint.get_hierarchy():
            parent = joint.get_parent()
            if parent and \
               (parent == root_joint or parent.is_child_of(root_joint)):
                self.tag_bind_joint(joint, parent=parent)
            else:
                self.tag_bind_joint(joint)

    def set_bind_skeleton(self):
        """Tags a sub-set of rig joints as the bind skeleton.
        By default, all joints in self.rig_skeleton are tagged
        (with hierarchy)

        Re-implement this method to customize the bind skeleton.

        Returns:
            None
        """
        for chain in self.rig_skeleton:
            for i, joint in enumerate(chain):
                if i > 0:
                    parent = chain[i - 1]
                else:
                    parent = joint.get_parent()
                    if not parent or not jutil.is_bind_joint(parent):
                        parent = None
                self.tag_bind_joint(joint, parent=parent)

    def aim_axis(self, chain_id=0):
        """Returns the aim axis of the joint chain at a given index."""
        aim_axis = None
        try:
            aim_axis = self.get_marker(chain_id, 0).aim_axis
        except BaseException:
            if self.__rig_skeleton:
                aim_axis = self.__rig_skeleton[chain_id][0].long_axis
        return aim_axis

    def is_aim_down(self, chain_id=0):
        """Checks if a given joint chain's aim axis is pointing down
        the chain.

        Args:
            chain_id (int): The joint chain index

        Returns:
            bool
        """
        aim_axis = self.aim_axis(chain_id)
        if aim_axis:
            return not aim_axis.startswith('-')
        return False

    # --- limb connection util methods

    @property
    def plug_nodes(self):
        """Returns the plug nodes in this limb.

        If no plug nodes are defined, use limb root.

        By default all plug nodes are connected to the parent limb
        in self.connect_parent().
        """
        plugs = self.__plugs
        if not plugs:
            return [self.limb_root.value]

    def add_plug(self, plug_node):
        """Makes a node as a plug node of this limb.

        By default all plug nodes are connected to the parent limb
        in self.connect_parent().
        """
        self.__plugs.append(Node(plug_node))

    # def get_parent_marker(self):
    #     """Returns the parent marker that this limb's marker
    #     system is connected to.

    #     Returns:
    #         Marker or None: The parent marker,
    #         or None if not found.
    #     """
    #     # from the child's marker system, find the parent marker
    #     child_ms = self.marker_system
    #     if child_ms:
    #         return child_ms.get_parent_marker()

    def _get_socket(self, marker):
        """From a marker node in this limb, returns the corresponding
        rig joint as the "socket" node to connect a child limb to.

        Returns:
            Joint or None: The socket joint, or None if not found.
        """
        if marker:
            # with the parent marker, try find the associated
            # result joint at the same ids.
            marker_sys = self.marker_system
            ids = marker_sys.get_marker_ids(marker)
            if ids[0] != -1:
                return self.rig_skeleton[ids[0]][ids[1]]

    def get_world_offset_limb(self):
        """Searches the graph this limb belongs to,
        find and returns the world offset limb action.

        Returns:
            WorldOffset or None: The world offset limb
            or None if not found.

        Raises:
            RuntimeError: If more than 1 world offset limb
                exists.
        """
        if self._source_limb:
            world_offset = self._source_limb.find_actions(
                type_='mhy:WorldOffset', from_root=True)
        else:
            world_offset = self.find_actions(
                type_='mhy:WorldOffset', from_root=True)
        if len(world_offset) > 1:
            raise RuntimeError(
                'More than 1 world offset limbs found: {}'.format(world_offset))
        elif world_offset:
            return world_offset[0]

    # --- limb connection event triggers.

    def get_parent_socket(self):
        """Finds the socket joint that this limb should be connected to.

        The socket joint is determined either by the marker system, or
        directly input from parameter "parent_joint", if not empty.

        Returns:
            Node or None: The parent socket joint, or None if not found.
        """
        # check parent joint override first
        socket = self.parent_joint.value
        if socket:
            if not cmds.objExists(socket):
                raise exp.ParameterError(
                    'Parent joint override not found: {}'.format(socket))
            return Node(socket)

        # find the parent marker via the marker system,
        # then find the parent's socket joint
        marker_sys = self.marker_system
        if marker_sys:
            parent_limb = self.get_parent_limb()
            parent_marker = marker_sys.get_parent_marker()
            return parent_limb._get_socket(parent_marker)

    def connect_parent(self, parent_limb):
        """Connects this limb to the parent limb's socket joint, if specified.

        The default behavior is to constrain this limb's root node to the
        socket joint.

        Called at the end of the limb execution. Re-implement this method
        to customize the connection behavior.

        Args:
            parent_limb (BaseLimb):
                The parent limb object to connect to. This value is auto-passed
                in by the child limb (Called in `self.end()`).

        Returns:
            None
        """
        socket = self.get_parent_socket()
        if socket:
            for plug in self.plug_nodes:
                self.add_constraint('parent', socket, plug, maintainOffset=True)

    def connect_parent_bind_skeleton(self, parent_limb):
        """Connects this limb's bind skeleton to its parent's bind skeleton.

        The default behavior is to connect the root bind joints of this limb
        to its parent's socket joint.

        If the socket is not a bind joint, use its closest bind joint instead.

        If _REPLACE_BIND_SOCKET is True, use the bind parent of the
        socket joint, then untag the socket joint at the end.

        Called at the end of the limb execution. Re-implement this method
        to customize the connection behavior.

        Args:
            parent_limb (BaseLimb):
                The parent limb object to connect to. This value is auto-passed
                in by the child limb (Called in `self.end()`).

        Returns:
            None
        """
        socket = self.get_parent_socket()
        if socket:
            if not jutil.is_bind_joint(socket):
                socket = jutil.get_closest_bind_parent(socket)

            remove_socket = None
            if self._REPLACE_BIND_SOCKET:
                remove_socket = socket
                socket = jutil.get_bind_parent(socket)

            if socket:
                for each in self.__root_bind_joints:
                    self.tag_bind_joint(each, parent=socket)

                if remove_socket:
                    parent_limb.untag_bind_joint(remove_socket)

    def connect_child(self, child_limb):
        """This method is triggered after a connect_parent() is called.
        It gives the parent limb a chance to customize its connection
        to the child limb.

        Args:
            child_limb (BaseLimb):
                The child limb object to connect to this limb.
                This value is auto-passed in by the parent limb.
                (Called in `self.end()`).

        Returns:
            None
        """
        return

    # --- execution method implementations

    def start(self):
        """Creates required top-level limb nodes.

        This is an optional execution method.
        It executes before self.run() is called.

        Raises:
            ActionError: If parameter "part" is empty.
            ActionError: If the limb root node already exists.
        """
        self._reset_private_vars()

        # ensure part token is not empty
        part = self.part.value
        if not part:
            raise exp.ActionError('Part token cannot be empty.')

        # ensures rig root groups exist
        util.init_rig_root_groups()

        # establish the rig skeleton by either process the input joints
        # or build the skeleton from maker system.
        if self.input_skeleton.value:
            self.resolve_input_skeleton()
        else:
            self.build_marker_skeleton()

        # create the limb root node
        self.debug('creating limb root node:')
        side = self.side.enum_value
        name = NodeName(part=part, desc='ROOT', side=side, ext='LIMB')
        # check if a limb with the same name already exists
        if cmds.objExists(name):
            raise exp.ActionError('Limb already exists: {}'.format(name))
        limb_root = Node.create(
            'MHYLimbRoot', name=name, limb_type=self.limb_type)
        limb_root.set_parent(const.LIMB_ROOT)
        self.limb_root.value = limb_root

        # add worldspace node and turn off inheritsTransform
        if self._REQUIRE_WS_ROOT:
            self.debug('creating limb worldspace root node:')
            name = NodeName(limb_root, ext=const.WS_NODE)
            self.__ws_root = Node.create('transform', name=name)
            self.__ws_root.set_parent(limb_root)
            self.__ws_root.inheritsTransform.value = False
            self.__ws_root.v.value = False

        # add ctrl root node
        self.debug('creating limb ctrl root node:')
        name = NodeName(limb_root, desc='ROOT', ext='CONTROL')
        self.__ctrl_root = Node.create('transform', name=name)
        self.__ctrl_root.set_parent(limb_root)

        # cache rig skeleton matrices for validation
        self.__cache_rig_skel_matrices()

    def end(self):
        """Cleans up this limb, trigger limb connection methods.
        If parameter `mirror` is set to True, build the mirrored limb.

        It executes after self.run() is called.
        """
        # sets the bind skeleton
        self.set_bind_skeleton()

        # create limb ctrl leaf node
        self.debug('creating limb ctrl leaf node:')
        name = NodeName(self.__ctrl_root, ext='LEAF')
        self.__ctrl_leaf = Node.create('transform', name=name)
        self.__ctrl_leaf.set_parent(self.ctrl_leaf_parent)

        # misc clean up operations
        self._set_outliner_color()

        # hook up vis attr
        self._setup_ctrl_vis()

        parent_limb = self.get_parent_limb()
        if parent_limb:
            # connection even callback:
            #
            # trigger an limb connection even callbacks
            self.connect_parent(parent_limb)
            self.connect_parent_bind_skeleton(parent_limb)
            parent_limb.connect_child(self)

            # parent this limb's root to its parent's ctrl leaf.
            hier_type = os.environ.get('MHY_RIG_HIER', 'nested')
            if hier_type == 'nested':
                ctrl_leaf = parent_limb.ctrl_leaf
                if ctrl_leaf:
                    self.limb_root.value.set_parent(ctrl_leaf)
            # parent this limb's root to world offset limb's ctrl leaf
            elif hier_type == 'flat':
                world_offset = self.get_world_offset_limb()
                if world_offset:
                    parent = world_offset.ctrl_leaf
                    self.limb_root.value.set_parent(parent)

            # link limbs to form a continuous ctrl hub network
            parent_limb_root = parent_limb.limb_root.value
            self.limb_root.value.connect_parent_limb(parent_limb_root)

        # checks if rig skeleton is changed after ctrl rig build
        self.__validate_rig_skel()

        # create a mirrored limb if requested
        if self.mirror.value:
            self.mirror_limb()

    def _setup_ctrl_vis(self):
        """Setup ctrl visibility switch."""
        attr = self._CTRL_VIS_ATTR
        if attr:
            rig_root = util.get_or_create_rig_root()
            if not rig_root.has_attr(attr):
                attr = rig_root.add_attr('bool', attr, defaultValue=True)
                attr.channelBox = True
            else:
                attr = rig_root.attr(attr)
            attr >> self.limb_root.value.v

    def mirror_limb(self, exec_name='main'):
        """Makes a copy of the this limb with mirrored parameter values
        and execute it.

        Args:
            exec_name (str): If "main", run the main execution.
                Otherwise run the specified custom execution.

        Returns:
            None
        """
        def flip_string(string):
            if string.find('_L_') >= 0:
                return string.replace('_L_', '_R_')
            elif string.find('_R_') >= 0:
                return string.replace('_R_', '_L_')
            else:
                return string

        def flip_list(in_list):
            out_list = []
            for val in in_list:
                if isinstance(val, (list, tuple)):
                    val = flip_list(val)
                elif isinstance(val, dict):
                    val = flip_dict(val)
                elif isinstance(val, string_types):
                    val = flip_string(val)
                out_list.append(val)
            return out_list

        def flip_dict(in_dict):
            out_dict = OrderedDict()
            for key, val in in_dict.items():
                if isinstance(val, (list, tuple)):
                    val = flip_list(val)
                elif isinstance(val, dict):
                    val = flip_dict(val)
                elif isinstance(val, string_types):
                    val = flip_string(val)
                out_dict[key] = val
            return out_dict

        # skip middle limbs
        side = self.side.enum_value
        if side == NodeName.SIDE_M:
            self.mirrored_limb.value = self
            return

        # make an independent copy of this limb
        self.debug('Mirroring limb: {}'.format(self.long_name))
        new_limb = self.copy(
            name=self.name + '_mirrored', graph=None, bake_script=True)
        self._mirrored_limb = new_limb
        new_limb._source_limb = self

        # flip parameters
        for param in new_limb.get_params(input_=True, output=False):
            ptype = param.param_type
            if param.name == 'side':
                if side == NodeName.SIDE_L:
                    param.value = NodeName.SIDE_R
                else:
                    param.value = NodeName.SIDE_L
            elif param.name == 'parent_limb':
                parent_limb = self.get_parent_limb()
                if parent_limb:
                    mirrored_parent = parent_limb._mirrored_limb
                    if not mirrored_parent:
                        mirrored_parent = parent_limb
                    new_limb._override_parent_limb(mirrored_parent)
            elif ptype == 'str':
                param.value = flip_string(param.value)
            elif ptype in ('list', 'iter'):
                param.value = flip_list(param.value)
            elif ptype == 'dict':
                param.value = flip_dict(param.value)

        # prevent mirroring cycle
        new_limb.mirror.value = False

        # execute mirrored limb
        new_limb.execute(exec_name=exec_name)
        self.mirrored_limb.value = new_limb

    # --- ctrl-related methods

    def add_ctrl(self, parent=None, **kwargs):
        """Builds a MHY ctrl object and add it to this limb.
        The name of the limb node will be tagged on every ctrl.

        Args:
            parent (str or Transform): A transform node to parent this ctrl to.
            kwargs : MHYCtrl creation kwargs. See ctrl.py for details.

        Returns:
            MHYCtrl: The ctrl object.
        """
        # create the ctrl node
        self.debug('- create ctrl:')
        kwargs['limb_root'] = self.limb_root.value
        ctrl = Node.create('MHYCtrl', **kwargs)

        # parent the ctrl
        if not parent:
            parent = self.__ctrl_root
        hook = ctrl.plc_node
        if not hook:
            hook = ctrl
        hook.set_parent(parent)

        return ctrl

    def add_constraint(self, ctype, *args, **kwargs):
        """Convenience method to add point, orient, or scale constraints.

        Args:
            ctype (str): The constraint type to add.
            args: A list of driver nodes and a driven node at the end.
            kwargs: keyword arguments accepted by `cmds.xxxConstraint()`.

        Returns:
            DependencyNode: The constraint node
        """
        self.debug('- add constraints')
        args = list(args[:])
        driven = Node(args.pop(-1))
        kwargs['name'] = NodeName(driven, ext=ctype.upper() + 'CONSTRAINT')
        c = driven.constrain(ctype, *args, **kwargs)
        self.__constraints.append(c)
        return c

    # --- clean up methods

    def _set_outliner_color(self):
        """set ctrl nodes color in outliner
        Set color for ctrl node and root/leaf nodes in outliner for
        easier managemant
        """
        self.debug('set color for limb root, ctrl root, and ctrl leaf.')
        for node, color in zip(
                (self.limb_root.value, self.__ctrl_root, self.__ctrl_leaf),
                (LIMB_ROOT_COLOR, CTRL_ROOT_COLOR, CTRL_LEAF_COLOR)):
            node.set_attr('useOutlinerColor', True)
            node.set_attr('outlinerColor', color)

    # --- misc utils

    def has_limb_attr(self, attr_name):
        """Checks if a limb attr exists.

        Args:
            attr_name (str): Name of the attribute to check.

        Returns:
            bool
        """
        return self.limb_root.value.shape.has_attr(attr_name)

    def add_limb_attr(self, typ, name='limb_attr', as_pose=False, **kwargs):
        """Adds an attribute on the limb shape node.
        If the attribute already exists, return it directly.

        Args:
            typ (str): The attribute type.
            name (str): The attribute name.
            as_pose (bool): If True mark this attr as a pose attr.
            kwargs: kwargs for cmds.addAttr()

        Returns:
            Attribute: The added attribute object.

        Raises:
            ActionError: If the limb shape node is not found.
        """
        # pose atts can not have whitespaces
        if as_pose:
            name = name.replace(' ', '')
        limb_root = self.limb_root.value

        # create the attribute
        if not limb_root.shape:
            raise exp.ActionError('Limb shape node not found.')
        if self.has_limb_attr(name):
            return limb_root.shape.attr(name)
            # raise exp.ActionError(
            #     'Limb attribute already exists: {}.{}'.format(
            #         limb_root.shape, name))
        attr = limb_root.shape.add_attr(typ, name=name, **kwargs)

        # mark the attr as a pose attr
        if as_pose:
            shape = limb_root.shape
            if not shape:
                raise exp.ActionError('Limb shape node not found.')

            pose_attr = 'poseDrivenAttributes'
            value = str(name)
            if not shape.has_attr(pose_attr):
                shape.add_attr('string', name=pose_attr)
            else:
                cur = shape.get_attr(pose_attr)
                if cur:
                    value = '{} {}'.format(cur, value)

            pose_attr = shape.attr(pose_attr)
            pose_attr.locked = False
            pose_attr.value = value
            pose_attr.locked = True

        return attr

    def add_nonkeyable_attr(self, *args, **kwargs):
        """Adds a non-keyable attr on the limb node.

        Args:
            args: Arguments accepted by add_limb_attr().
            kwargs: Keyword arguments accepted by add_limb_attr().

        Returns:
            Attribute: The added attribute object.
        """
        if 'k' in kwargs:
            kwargs.pop('k')
        kwargs['keyable'] = False
        attr = self.add_limb_attr(*args, **kwargs)
        attr.channelBox = True
        attr.locked = kwargs.get('lock', False)
        return attr

    def create_ribbon(
            self, start, end, attach_amount=3, long_axis=None, mode='start', avoid_overlap=False):
        """Creates a ribbon setup.

        A ribbon surface with 2 ends attached to the given start joint and
        end joint respectively. A series of follicles are attached to the
        surface to drive bind joints.

        Args:
            start (str or Node): The start joint to attach the ribbon to.
            end (str or Node): The end joint to attach the ribbon to.
            attach_amount (int): The number of follicles to attach to
                the ribbon surface.
            long_axis (str): The rig joint chain's long axis.
                If None, calculate the long axis automatically.
            mode (str): The way to locate the follicles. 'start' means
                put the first follicle at start of the ribbon, no
                follicle at the end. 'end' mean last follicle at end
                of the ribbon, no follicle at the start. 'start_end'
                means put follicle at both ends. 'mid' means no follicle
                will be put on the ends.
            avoid_overlap (bool): Set to True, when you need to avoid
                overlap at the end of the joint.

        Returns:
            (root node,
            start offset node,
            mid ctrl node,
            end_offset node,
            follicle list)
        """
        rot_dict = {'Y': ('Z', 90), 'Z': ('Y', -90)}
        start_joint = Node(start)
        end_joint = Node(end)
        length = mmath.distance(start_joint, end_joint)
        if start_joint.long_axis.startswith('-'):
            length *= -1

        if avoid_overlap:
            w = 0.05
            factor = 0.9
        else:
            w = 0
            factor = 1
        base_name = NodeName(start_joint, ext='GRP')
        desc = base_name.desc + 'Ribbon'
        base_name = base_name.replace_desc(desc)
        root = Node.create('transform', name=base_name)

        name = base_name.replace_ext('OFFSET')
        offset = Node.create('transform', name=name, parent=root)

        name = base_name.replace_ext('RIGJNT')
        jnt_list = []
        cmds.select(clear=True)
        for i in range(3):
            name = name.replace_num(i)
            jnt = Node.create(
                'joint', name=name,
                position=(length * i / 2.0, 0, 0), absolute=True)
            jnt_list.append(jnt)
            jnt.set_parent(root)
        name = name.replace_num(0)

        # create ribbon nurbs surf
        name = base_name.replace_ext('SURF')
        surf, make_surf = cmds.nurbsPlane(
            name=name, axis=[0, 1, 0], p=[0.5 * length, 0, 0],
            u=2, w=length, lr=0.2)
        cmds.rebuildSurface(
            surf, spansU=2, spansV=1, degreeU=3, degreeV=1, keepRange=0)
        surf = Node(surf)
        surf.set_parent(root)
        make_surf = Node(make_surf)
        make_surf.name = 'make' + name

        # skin bind surf
        name = base_name.replace_ext('SKINCLUSTER')
        cmds.select(clear=True)
        skc = cmds.skinCluster(jnt_list, surf, name=name)[0]
        cmds.skinPercent(
            skc, surf.name + '.cv[0][0:1]', tv=[(jnt_list[0], 1)])
        cmds.skinPercent(
            skc, surf.name + '.cv[1][0:13]',
            tv=[(jnt_list[0], 0.67), (jnt_list[1], 0.33)])
        cmds.skinPercent(
            skc, surf.name + '.cv[2][0:1]', tv=[(jnt_list[1], 1)])
        cmds.skinPercent(
            skc, surf.name + '.cv[3][0:1]',
            tv=[(jnt_list[1], 0.33), (jnt_list[2], 0.67)])
        cmds.skinPercent(
            skc, surf.name + '.cv[4][0:1]', tv=[(jnt_list[2], 1)])

        # create start locator
        name = NodeName(base_name, desc=base_name.desc + 'Start', ext='OFFSET')
        start_offset = Node.create('transform', name=name, parent=offset)
        name = name.replace_ext('LOC')
        start_loc = Node.create('transform', name=name, parent=start_offset)
        jnt_list[0].set_parent(start_loc)

        # create mid locator
        name = NodeName(base_name, desc=base_name.desc + 'Mid', ext='OFFSET')
        mid_offset = Node.create('transform', name=name, parent=start_offset)

        name = name.replace_ext('IKCTRL')
        mid_ctrl = self.add_ctrl(
            name=name,
            parent=mid_offset,
            rot=(0, 0, 90),
            color=(1, 1, 0),
            shape='circle')

        self.add_constraint(
            'parent', mid_offset, mid_ctrl.plc_node, maintainOffset=True)
        mid_offset.tx.value = .5 * length
        jnt_list[1].set_parent(mid_ctrl)

        # create end locator
        name = NodeName(base_name, desc=base_name.desc + 'End', ext='OFFSET')
        end_offset = Node.create('transform', name=name, parent=start_offset)
        name = name.replace_ext('LOC')
        end_loc = Node.create('transform', name=name, parent=end_offset)
        end_offset.tx.value = length

        jnt_list[2].set_parent(end_loc)

        # setup ribbon position
        offset.parent_align(start_joint)
        if not long_axis:
            long_axis = start_joint.long_axis
        if long_axis and long_axis[-1] != 'X':
            offset.set_attr(
                'rotate' + rot_dict[long_axis[-1]][0],
                rot_dict[long_axis[-1]][1])
        self.add_constraint(
            'point', start_offset, end_offset, mid_offset, maintainOffset=True)
        long_axis_num = {'X':0, 'Y':1, 'Z':2, '-X':0, '-Y':1, '-Z':2}
        self.add_twist_node(driver=end_offset, driven=mid_offset, twist=0.5, swing=0, twistAxis=long_axis_num[long_axis])

        # attach follicles
        name = base_name.replace_ext('FOLLICLE')
        flcs_list = []
        for i in range(0, attach_amount):
            if mode == 'start':
                num = float(i)
                den = attach_amount
            elif mode == 'end':
                num = float(i + 1)
                den = attach_amount
            elif mode == 'start_end':
                num = float(i)
                den = attach_amount - 1
            elif mode == 'mid':
                num = float(i + 1)
                den = attach_amount + 1

            if den == 0:
                raise RuntimeError('If attach_mount = 1, you can not set mode to "start_end"!')

            name = name.replace_num(i)
            flc_shape = Node.create('follicle', surf, name=name)
            flc_shape.parameterV.value = 0.5
            flc_shape.parameterU.value = w + num / den * factor
            flc_xform = flc_shape.get_parent()
            flc_xform.set_parent(root)
            flcs_list.append(flc_xform)

        return root, offset, start_offset, mid_ctrl, end_offset, flcs_list

    def add_twist_node(self, driver=None, driven=None, twist=1, swing=0, twistAxis=0):
        """build up twsit node base on twistSwing node

        Args:
            driver (str): the driver obj
            driven (str): the driven obj
            twsit (float): the twist weight -1 to 1
            swing (float): the swing weight -1 to 1
            twistAxis (int): 0:X, 1:Y, 2:Z
        """
        name = NodeName(driver, ext='TWNODE')
        twist_node = cmds.swingTwist(
            driver, driven, twist=twist, swing=swing,
            twistAxis=twistAxis, name=name)
        twist_node = Node(twist_node)
        return twist_node

    def create_ik_chain(
            self, start_joint=None, end_joint=None,
            pole_vector=None, parent=None):
        """Creates an IK chain with 3 or more joints chain.
        The pole vector will be alain with the first second and last joint.

        Args:
            start_joint (str): TODO
            end_joint (str): TODO
            pole_vector (str): The object at the pole vector position
                If None, auto-calculate a pole vector position.
            parent (str): The parent object the ik chain will be parent to

        Returns:
            tuple: ik handle and the group of pole vector control.
        """
        joint_chain = jutil.JointChain(start=start_joint, end=end_joint)

        # create ik handle
        name = NodeName(joint_chain[0], ext='IKHDL')
        handle, effector = cmds.ikHandle(
            name=name, sticky=True,
            startJoint=joint_chain[0], endEffector=joint_chain[-1])
        handle = Node(handle)
        handle.v.value = False
        if parent:
            handle.set_parent(parent)
        name = name.replace_ext('EFF')
        cmds.rename(effector, name)

        # get polve vector positon
        if not pole_vector:
            p_vector = joint_chain.get_pole_vector()
        else:
            p_vector = cmds.xform(
                pole_vector, query=True, worldSpace=True, translation=True)

        # set up up vector
        name = name.replace_ext('VEC')
        vec = Node.create('transform', name=name, parent=parent)
        vec.set_translation(p_vector, space='world')
        self.add_constraint('poleVector', vec, handle)

        return handle, vec
