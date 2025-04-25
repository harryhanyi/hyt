import maya.cmds as cmds

from mhy.maya.standard.name import NodeName
from mhy.maya.nodezoo.node import Node
import mhy.maya.rig.constants as const
import mhy.maya.rig.joint_utils as jutil
import mhy.maya.rig.face.tracer as tracer
from mhy.maya.rig.utils import add_influence_tag_attribute
from mhy.maya.rig.utils import xform_connect


class ParameterDriverSystem(object):
    """
    TODO doc
    """

    def __init__(
            self,
            joints=None,
            build_tracer = 'parameter',
            ws_root=const.WS_NODE):
        """
        
        Args:
            joints (list):
                A list of joints which the parameter driver system will be built on.
                
            build_tracer (str or None):
                Options:
                parameter - build parameter tracer handle on each given joint and ctrl.
                wordspace - build worldspace tracer handle on each given joint and ctrl.
                None - skip tracer handle building.
        """

        self.build_tracer = build_tracer
        self.ws_root = Node(ws_root)
        self.influences=[]

        if not joints:
            joints = jutil.get_joints_in_category('bind')
            self.influences = jutil.get_joints_in_category(
                'influence', joints=joints)
        else:
            for jnt in joints:
                if not cmds.objExists(jnt):
                    cmds.warning(
                        '{} does not exists in scene, skip.'.format(jnt))
                else:
                    self.influences.append(Node(jnt))

        pds_null = 'paramDriverSystem'
        pds_flc_null = 'pds_follicle'
        
        if not cmds.objExists(pds_null):
            self.pds_null = Node.create(
                'transform', name=pds_null, parent=self.ws_root) 
        else:
            self.pds_null = pds_null
        
        if not cmds.objExists(pds_flc_null):
            self.pds_flc_null = Node.create(
                'transform', name='pds_follicle', parent=self.pds_null)
            self.pds_null.lock('trs')
            #self.pds_flc_null.v.value = False
            self.pds_flc_null.lock('trs')
        else:
            self.pds_flc_null = pds_flc_null

        self.cpos = None
        self.inf = None
        self.ctrl = None
        self.facial_xform = None
        self.parent_node = None
        self.param_patch = None
        self.patch_shape = None
        self.pds_patch_list = []
        self.inf_ctrl_dict = {}
        self.flc_nodes=[]
        self.flc_tranforms=[]
        self.tracer_han = None

        patch_tag = 'parameter'
        for inf in self.influences:
            ctrl = jutil.get_ctrl(inf)

            if not ctrl:
                raise RuntimeError(
                    'Joint {} not associated with any ctrl.'.format(inf))
            if not inf.has_attr(patch_tag):
                raise RuntimeError('Attribute {} not exists on {}.'.format(
                    patch_tag, inf))

            patch = inf.get_tag(patch_tag)
            self.inf_ctrl_dict[inf] = (ctrl, Node(patch))


    def build(self):
        """TODO doc"""

        self.cpos = Node.create('closestPointOnSurface')

        # build parameterUV control system
        for self.inf in self.influences:

            self.facial_xform, self.param_patch = self.inf_ctrl_dict[self.inf]
            self.plc_node = self.facial_xform.plc_node
            self.parent_node = self.plc_node.get_parent()
            if not self.parent_node:
                raise RuntimeError(
                    ('Facial transform plc node {} dose not have '
                     'a parent.').format(self.plc_node))

            self.patch_shape = self.param_patch.get_shapes()[0]
            self.patch_shape.worldSpace[0] >> self.cpos.inputSurface

            if self.param_patch not in self.pds_patch_list:
                self.pds_patch_list.append(self.param_patch)
                
            self.ctrl = self.inf_ctrl_dict[self.inf][0]

            self.create()

        # cleanup
        cmds.delete(self.cpos)


    def create(self):
        """TODO doc"""
        # get original u,v values
        inf_pos = self.inf.get_translation(space='world')
        self.cpos.set_attr('inPosition', inf_pos)
        u = self.cpos.parameterU.value
        v = self.cpos.parameterV.value

        # create joint's flc on patch
        flcname = NodeName(self.inf, ext='FLCTRANSFORM')
        flc = Node.create('follicle', self.patch_shape, name=flcname)
        flc.name = flcname.replace_ext('FLC')
        flc_trans = flc.get_parent()
        self.flc_nodes.append(flc)
        self.flc_tranforms.append(flc_trans)
            
        # tag flc data to inf
        attr = 'flc'
        if not cmds.attributeQuery(attr, node=self.inf, ex=True):
            self.inf.add_attr('string', name='flc', keyable=False)
        attr_flc = self.inf.attr('flc')
        attr_flc.locked = False
        attr_flc.value = flc.name
        attr_flc.locked = True
        
        attr = 'originU'
        if not cmds.attributeQuery(attr, node=self.inf, ex=True):
            self.inf.add_attr('float', name=attr, keyable=False)
        attr_u = self.inf.attr(attr)
        attr_u.locked = False
        attr_u.value = u
        attr_u.locked = True
        
        attr = 'originV'
        if not cmds.attributeQuery(attr, node=self.inf, ex=True):
            self.inf.add_attr('float', name=attr, keyable=False)
        attr_v = self.inf.attr(attr)
        attr_v.locked = False
        attr_v.value = v
        attr_v.locked = True

        # Op.1 - build parameter tracer
        # build tracer handles at the orig
        if self.build_tracer == 'parameter':
            TRACER = tracer.ParameterTracer(
                self.param_patch, name=NodeName(self.inf, ext='TRACER'))
            tracer_han = TRACER.create()
        
            # move and connect tracer to flc
            tracer_han.parameterU >> flc.parameterU
            tracer_han.parameterV >> flc.parameterV
            tracer_han.parameterU.value = u
            tracer_han.parameterV.value = v
            self.tracer_han = Node(tracer_han)
        
        # Op.2 - build worldspace tracer
        elif self.build_tracer == 'worldspace':
            tracer_han = Node.create(
                'MHYCtrl',
                name=NodeName(self.inf, ext='TRACER'),
                shape='sphere',
                pos=(0, 0, 0.1),
                scale=(0.025, 0.025, 0.025),
                color=(0,1,1),
                group_exts=('PLC', 'INVERSE'))
                
            tracer_han.plc_node.align(self.ctrl)
            tracer_han.plc_node.set_parent(self.ctrl)
            tracer_han.plc_node.lock('rsv')
            
            # setup inverse
            xform_connect(
                tracer_han,
                tracer_han.inverse_node,
                attrs='t',
                inverse=True,
                lock=True)
                
            # create alias and clean up
            tracer_han.translateX.alias = 'parameterU'
            tracer_han.translateY.alias = 'parameterV'
            tracer_han.lock('rsv')
            tracer_han.lock('tz')
            self.tracer_han = Node(tracer_han)
                
            # connect ws tracer to flc
            adl_u = Node.create('addDoubleLinear', name=NodeName(flc, ext='_adlU'))
            adl_u.input2.value = u
            tracer_han.parameterU >> adl_u.input1
            adl_u.output >> flc.parameterU
            
            adl_v = Node.create('addDoubleLinear', name=NodeName(flc, ext='_adlV'))
            adl_v.input2.value = v
            tracer_han.parameterV >> adl_v.input1
            adl_v.output >> flc.parameterV
        
        # Op.3 - build flc without tracer handle
        # leave flc parameter u & v attributes
        # at the original value, not connected
        else:
            flc.set_attr('parameterU', u)
            flc.set_attr('parameterV', v)
        
        
        # set origin UV values and add driven attr dict for tracer only
        if self.build_tracer:
            driven_attr_value={}
            for ch, val in zip('UV', (u, v)):
                attr = self.tracer_han.add_attr('string', name='origin'+ch)
                attr.locked = False
                attr.value = val
                attr.locked = True
                driven_attr_value['parameter{}'.format(ch)] = {'neutral': 0.0}

            add_influence_tag_attribute(self.tracer_han, driven_attr_value)
        
        # insert sys to ctrl heirarchy
        transport_orig = Node.create(
            'transform', parent=self.parent_node,
            name=NodeName(self.inf, ext='ORIGIN'))
        transport_node = Node.create(
            'transform', parent=transport_orig,
            name=NodeName(self.inf, ext='TRANSPORT'))

        # connect from follicle output to transport node
        for ch in ('translate', 'rotate'):
            for ax in 'XYZ':
                flc_trans.attr(ch + ax) >> transport_node.attr(ch + ax)

        self.plc_node.set_parent(transport_node)
        flc_trans.set_parent(self.pds_flc_null)
        
        
