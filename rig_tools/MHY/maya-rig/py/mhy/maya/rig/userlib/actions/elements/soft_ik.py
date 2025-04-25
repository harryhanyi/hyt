from mhy.protostar.core.action import MayaAction
import maya.cmds as cmds
from mhy.maya.nodezoo.node import Node
from mhy.maya.standard.name import NodeName
import mhy.maya.maya_math as mmath
import mhy.maya.rig.joint_utils as jutil
import mhy.protostar.core.parameter as pa

# Add soft ik to 3 bone ik chain
# ik_chain: tuple or list of 3 bone chain
# ple_vec: the pole vec of the ik chain

class Soft_IK(MayaAction):
    """
    An action to create soft ik for 3 bone ik chain.
    """
    @pa.str_param()
    def limb(self):
        """A parent limb action to connect this limb to."""

    @pa.list_param()
    def joint_chain(self):
        """The start joint, and end joint of the 3 bone rig joint."""

    @pa.str_param()
    def end_joint(self):
        """The start joint, and end joint of the 3 bone rig joint."""
    
    @pa.enum_param(items=('mid_ctrl','IK_chain'), default='mid_ctrl')
    def method_type(self):
        """The mid_ctrl is the default soft ik method, more method will be added."""

    @pa.bool_param(default=True)
    def set_limb_attr(self):
        """Add soft ik attrs to limb root or not."""
    
    @pa.bool_param(default=True)
    def connect_to_IK_blend(self):
        """connect the soft ik to IK blend parameter, so soft ik will switch with IKFK."""

    @pa.bool_param(default=False)
    def mirror(self):
        """create mirror soft ik"""

    def run(self):
        self._reset_params()
        self.create()
        if self.mirror.value:
            self.mirror_params()
            self.create()
        

    def _reset_params(self):
        self.limb_name = self.limb.value
        self.joint_list = self.joint_chain.value[:]

    def mirror_params(self):
        if '_L_' in self.limb_name:
            side = '_L_'
            mirror_side = '_R_'
        elif '_R_' in self.limb_name:
            side = '_R_'
            mirror_side = '_L_'
        elif '_M_' in self.limb_name:
            raise ValueError('{} is a middle limb, which can not be mirrored.'.format(self.limb_name))
        self.limb_name = self.limb_name.replace(side, mirror_side)
        chain = [j.replace(side, mirror_side) for j in self.joint_list]
        self.joint_list = chain
        return

    def create(self):
        self.limb_root = Node(self.limb_name)
        self.type = self.method_type.enum_value
        self.chain = [Node(j) for j in self.joint_list]
        if len(self.chain)!=3:
            raise ValueError('The ik_chain has to be 3 bone chain.')

        start_joint = self.chain[0]
        mid_joint = self.chain[1]
        end_joint = self.chain[2]
        start_pnt = start_joint.get_translation(space='world', as_tuple=False)
        mid_pnt = mid_joint.get_translation(space='world', as_tuple=False)
        end_pnt = end_joint.get_translation(space='world', as_tuple=False)
        vec_pos = jutil.JointChain(start_joint, end_joint).get_pole_vector()

        #Get upper limb and lower limb longth
        upper_length = mmath.distance(start_pnt, mid_pnt)
        lower_length = mmath.distance(mid_pnt, end_pnt)
        length = upper_length + lower_length

        #Create root and locators
        name = NodeName(start_joint, desc='softIK', ext='ROOT')
        self.name = name
        self.root = Node.create('transform', name=name)
        self.root.align(start_joint)
        if cmds.objExists(self.limb_root):
            self.root.set_parent(self.limb_root)
        #The locator dirct to the end joint.
        drc = Node.create('transform', name=name.replace_ext('DRC'), parent=self.root)
        drc.align(self.root)
        #The locator at the final position of mid joint or ctrl
        self.final_loc = Node.create('transform', name=name.replace_ext('FNLOC'), parent=drc)
        self.final_loc.align(drc)
        self.final_loc.tx.value = upper_length
        #Vector to guide the drc locator 
        vec = Node.create('transform', name=name.replace_ext('VEC'), parent=self.root)
        vec.set_translation(vec_pos, space='world')
        vec.constrain('parent', start_joint, maintainOffset=True)
        drc.constrain('aim', end_joint, maintainOffset=False, aimVector=[1,0,0], upVector=(0,0,-1), worldUpType='object', worldUpObject=vec)
        self.target_loc = Node.create('transform', name=name.replace_ext('TGTLOC'), parent=self.root)
        start_loc = Node.create('transform', name=name.replace_ext('STARTLOC'), parent=drc)
        start_loc.align(drc)
        mid_loc = Node.create('transform', name=name.replace_ext('MIDLOC'), parent=start_loc)
        mid_loc.align(start_loc)
        mid_loc.tx.value = upper_length
        
        # Create attributes 
        self.angle = self.root.add_attr('float', name='soft_ik_start_angle',defaultValue=15, minValue=0, maxValue=30, keyable=False)
        self.angle >> start_loc.ry
        self.merge = self.root.add_attr('float', name = 'soft_ik_merge', defaultValue=0.1, minValue=0, maxValue=0.5, keyable=False)
        self.scale_factor = self.root.add_attr('float', name='scale_factor', defaultValue=1, minValue=0, keyable=True)
        self.switch = self.root.add_attr('float', name='soft_ik', defaultValue=0, minValue=0, maxValue=1, keyable=True)

        # Setup constraints
        tgt_cns = self.target_loc.constrain('point', mid_loc, self.final_loc, maintainOffset=False)

        # Buildup node graph
        orign_dist = Node.create('distanceBetween',name=name.replace_ext('ORGNDIST'))
        start_joint.worldMatrix[0] >> orign_dist.inMatrix1
        end_joint.worldMatrix[0] >> orign_dist.inMatrix2
        soft_rmp = Node.create('remapValue', name=name.replace_ext('SOFTRMP'))
        self.soft_merge_rmp = Node.create('remapValue', name=name.replace_ext('SOFTMENRMP'))

        script = """$angle = deg_to_rad({});
$max = {};
$upper = {};
$lower = {};
$y = $upper*cos($angle)+$lower*cos(asin($upper/$lower*sin($angle)));
$delta_y = ($max-$y)*{}+$y;
{} = $y*{};
{} = {};
{} = $delta_y*{};""".format(self.angle, length, upper_length, lower_length, self.merge, soft_rmp.inputMin, self.scale_factor, 
            self.soft_merge_rmp.inputMin, soft_rmp.inputMin, self.soft_merge_rmp.inputMax, self.scale_factor)
        cmds.expression(string=script, name=name.replace_ext('SOFTIKCAL'))       
        soft_rmp.inputMax.value=length
        orign_dist.distance >> soft_rmp.inputValue
        orign_dist.distance >> self.soft_merge_rmp.inputValue
        soft_sub = Node.create('plusMinusAverage', name=name.replace_ext('SOFTSUB'))
        soft_sub.operation.value = 2
        soft_sub.input1D[0].value = 1
        soft_rmp.outValue >> soft_sub.input1D[1]
        soft_sub.output1D >> tgt_cns.attr('{}W0'.format(mid_loc))
        soft_rmp.outValue >> tgt_cns.attr('{}W1'.format(self.final_loc))
        self.merge_sub = Node.create('plusMinusAverage', name=name.replace_ext('SOFTMENSUB'))
        self.merge_sub.operation.value = 2
        self.merge_sub.input1D[0].value = 1
        self.soft_merge_rmp.outValue >> self.merge_sub.input1D[1]

        if self.set_limb_attr.value:
            self.add_limb_attr()
        if self.connect_to_IK_blend:
            self.connect_ik_blend()
        self.setup_type()
        return 
    
    # setup attrs on limb root shape node and connect to the soft ik root attrs
    def add_limb_attr(self):  
        
        if self.limb_root.api_type_str == 'MHYLimbRoot':
            switch = self.limb_root.shape.add_attr('float', name = 'soft_ik', defaultValue=0, minValue=0, maxValue=1, keyable=True)
            angle = self.limb_root.shape.add_attr('float', name = 'soft_ik_start_angle', defaultValue=15, minValue=0, maxValue=30, keyable=False)
            merge = self.limb_root.shape.add_attr('float', name = 'soft_ik_merge', defaultValue=0.1, minValue=0, maxValue=0.5, keyable=False)           
            angle.channelBox = True
            merge.channelBox = True
            switch >> self.switch
            angle >> self.angle
            merge >> self.merge
            self.limb_root.sx >> self.scale_factor
        else:
            raise TypeError('{} is not a limb root.'.format(self.limb_root))
        return

    # To find the soft ik type and running the right setup
    def setup_type(self):
        if self.type == 'mid_ctrl':
            self.connect_mid_ctrl()
        return

    def connect_mid_ctrl(self):
        start_joint = self.chain[0]    
        mid_joint = self.chain[1]
        name = NodeName(self.name, ext='TRANSLOC')
        trans_loc = Node.create('transform', name=name, parent=self.root)
        trans_cns = trans_loc.constrain('point', mid_joint, self.target_loc, maintainOffset=False)
        self.merge_sub.output1D >> trans_cns.attr('{}W0'.format(mid_joint))
        self.soft_merge_rmp.outValue >> trans_cns.attr('{}W1'.format(self.target_loc))
        switch_sub = Node.create('plusMinusAverage', name=name.replace_ext('TRANSUB'))
        switch_sub.operation.value = 2
        switch_sub.input1D[0].value = 1
        self.switch >> switch_sub.input1D[1]

        #Stretch setup
        stretch_dist = Node.create('distanceBetween', name=name.replace_ext('STDIST'))
        start_joint.worldMatrix[0] >> stretch_dist.inMatrix1
        mid_joint.worldMatrix[0] >> stretch_dist.inMatrix2
        stretch_dist.distance >> self.final_loc.tx

        cns = cmds.listConnections(mid_joint, destination=True, source=False, type='pointConstraint')[0]
        sdk = cmds.listConnections(cns, destination=True, source=False, type='transform', exactType=True)[0]
        cns = Node(cns)
        sdk = Node(sdk)
        sdk.constrain('point', trans_loc, maintainOffset=False)
        switch_sub.output1D >> cns.attr('{}W0'.format(mid_joint))
        self.switch >> cns.attr('{}W1'.format(trans_loc))
        
        self.root.constrain('point', self.chain[0], maintainOffset=False)
        return

    def connect_ik_blend(self):
        name = NodeName(self.name, ext='IKBLNDMLT')
        ik_blend_mlt = Node.create('multiplyDivide', name = name)
        try:
            self.limb_root.shape.IKFKBlend >> ik_blend_mlt.input1X            
        except:
            raise RuntimeError('There is no IKFKBlend attribute is on limb shape.')
        self.switch >> ik_blend_mlt.input2X
        self.switch = ik_blend_mlt.outputX
        return
