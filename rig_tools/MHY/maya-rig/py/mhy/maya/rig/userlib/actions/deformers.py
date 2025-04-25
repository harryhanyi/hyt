import maya.cmds as cmds
import maya.mel as mel

import mhy.protostar.core.parameter as pa
import mhy.protostar.core.exception as exp

from mhy.maya.rig.base_actions import BaseRigDataAction
import mhy.maya.rig.constants as const
from mhy.maya.nodezoo.node import Node
from mhy.maya.nodezoo.node.blend_shape import BlendShape
from mhy.maya.nodezoo.node.wrap import ProximityWrap


class CreateBlendShape(BaseRigDataAction):
    
    @pa.str_param(default=None)
    def base_geo(self):
        """The name of the geo that will be deformed."""
        
    @pa.str_param(default=None)
    def target_geo(self):
        """A list of target geos."""
           
    @pa.bool_param(default=False)
    def front_of_chain(self):
        """blendShape flag frontOfChain"""
        
    @pa.str_param(default=None)
    def deformer_name(self):
        """
        1. The name of the created blend shape deformer.
        2. If name is not given, will use the name of the base geo + ext.
        """

    @pa.str_param(default=None)
    def deformer_node(self):
        """
        1. The node object of the created blend shape.
        2. It's queryable after build.
        """
        
    @pa.float_param(default=1.0)
    def weight(self):
        """
        Default bs weight
        """
        
        
    def run(self):
        """
        Executes CreateBlendShape.
        """
        base = self.base_geo.value
        target = self.target_geo.value
        foc = self.front_of_chain.value
        deformer_name = self.deformer_name.value
        weight = self.weight.value
        
        if not deformer_name:
            deformer_name = '{}_BLENDSHAPE'.format(base)
        
        bs_node = BlendShape.create(
                        target, base, 
                        frontOfChain=foc,
                        name=deformer_name )
                        
        if weight:
            bs_node.set_target_weight(target, weight)
        
        self.deformer_node.value = bs_node



class CreateProximityWrap(BaseRigDataAction):

    @pa.str_param()
    def driven(self):
        """The name of the slave object."""

    @pa.str_param()
    def driver(self):
        """The name of the master object."""

    @pa.str_param(default='PROXY_MESH')
    def rig_node_parent(self):
        """
        The name of the group node
        where the clean mesh will be under.
        """

    @pa.str_param(default=None)
    def wrapMode(self):
        """
        Config wrapMode attribute on proximity wrap
        """

    @pa.int_param(default=5)
    def maxDrivers(self):
        """
        Config maxDrivers attribute on proximity wrap
        """

    @pa.float_param(default=0.0)
    def falloffScale(self):
        """
        Config falloffScale attribute on proximity wrap
        """

    @pa.int_param(default=0)
    def smoothInfluences(self):
        """
        Config smoothInfluences attribute on proximity wrap
        """

    @pa.int_param(default=0)
    def smoothNormals(self):
        """
        Config smoothNormals attribute on proximity wrap
        """

    @pa.bool_param(default=False)
    def driverBindGeo(self):
        """
        Replace DriverBindGeo on proximity wrap node.
        This is to fix the bug in current proximity wrap
        """

    @pa.str_param(default=None)
    def deformer_name(self):
        """
        1. The name of the created proximity wrap node.
        2. The driven object name will be used if None.
        3. It's queryable after build.
        """

    @pa.str_param(default=None)
    def deformer_node(self):
        """
        1. The node object of the created proximity wrap.
        2. It's queryable after build.
        """

    def run(self):
        """
        Executes CreateProximityWrap.
        """
        driven_obj = self.driven.value
        driver_obj = self.driver.value
        parent_node = self.rig_node_parent.value
        wrap_mode = self.wrapMode.value
        max_drivers = self.maxDrivers.value
        falloff_scale = self.falloffScale.value
        smooth_influences = self.smoothInfluences.value
        smooth_normals = self.smoothNormals.value
        driverBindGeo = self.driverBindGeo.value
        driver_bind_geo = None
        deformer_name = self.deformer_name.value

        if driverBindGeo:
            clean_geo = Node(driver_obj).duplicate(name='{}_DUP'.format(driver_obj))[0]
            clean_geo.unlock('trs')
            clean_geo.v.value = False
            clean_geo.set_parent(parent_node)
            driver_bind_geo = clean_geo

        if not deformer_name:
            deformer_name = '{}_PRXWRAP'.format(driven_obj)
            self.deformer_name.value = deformer_name

        prx_wrap = ProximityWrap.create(
                        driven_obj,
                        driver_obj,
                        wrapMode=wrap_mode,
                        maxDrivers=max_drivers,
                        falloffScale=falloff_scale,
                        smoothInfluences=smooth_influences,
                        smoothNormals=smooth_normals,
                        driverBindGeo=driver_bind_geo,
                        name=deformer_name )
        
        self.deformer_node.value = prx_wrap
