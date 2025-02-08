import maya.api.OpenMaya as om
import maya.api.OpenMayaAnim as oma
import maya.mel as mel
import maya.cmds as cmds

class WeightTools():
    def __init__(self):
        self.selection = cmds.ls(sl=1, fl=1)
        self.comp = list()
        self.joints = list()
        self.orig_mesh = None
        self._dup_mesh = None
    
    @staticmethod    
    def get_skincluster(obj):
        skin = mel.eval('findRelatedSkinCluster '+obj)
        sel_list = om.MSelectionList().add(skin)
        MObj = sel_list.getDependNode(0)
        MSkin = oma.MFnSkinCluster(MObj)
        
        return skin, MSkin
    
    @staticmethod    
    def copyJointInfluences(mesh_list=None):
        if mesh_list:
            selected = mesh_list
        else:
            selected = cmds.ls(sl = 1)

        if len(selected) == 2:
            source = selected[0]
            destination = selected[1]
            
            sourceSkin = mel.eval('findRelatedSkinCluster '+source)
            influences = cmds.skinCluster(sourceSkin,query=True,inf=True)
            
            cmds.skinCluster(influences,destination,tsb=True)
            destSkin = mel.eval('findRelatedSkinCluster '+destination)
            cmds.copySkinWeights(ss=sourceSkin, ds=destSkin, noMirror=True, surfaceAssociation='closestPoint', influenceAssociation='closestJoint')
            cmds.skinCluster(destSkin, forceNormalizeWeights=True, edit=True)
        else:
            print ("Must select a source skin and a target skin")
            
    def get_mcomp(self, comp):
        cmds.select(comp, replace=True)
        MSel_list = om.MGlobal.getActiveSelectionList()
        comp_dag, comp_mobj = MSel_list.getComponent(0)
        return comp_dag, comp_mobj
    
    def get_mesh_from_comp(self, comp):
        comp_dag = self.get_mcomp(comp)[0]
        #get mesh
        mesh_mobj = comp_dag.transform()
        mesh_node = om.MFnDependencyNode(mesh_mobj)
        return mesh_node.name()
    
    def dup_weight_to_comp(self):
        verts_num = len(self.comp)
        dup_sel_list = om.MSelectionList()
        dup_mesh_mobj = dup_sel_list.add(self._dup_mesh).getDagPath(0)
        
        dup_verts = list(i.replace(self.orig_mesh, self._dup_mesh) for i in self.comp)
        cmds.select(dup_verts, replace=True)
        dup_MSel_list = om.MGlobal.getActiveSelectionList()
        dup_comp_mobj = dup_MSel_list.getComponent(0)[1]
        dup_skin = self.get_skincluster(self._dup_mesh)[1]
        
        #get dup weight
        dup_infs = dup_skin.influenceObjects()
        dup_weights = dup_skin.getWeights(dup_mesh_mobj, dup_comp_mobj)[0]

        #get skincluster
        skin, MSkin = self.get_skincluster(self.orig_mesh)
        for jnt in self.joints:
            if jnt not in cmds.skinCluster(skin,query=True,inf=True):
                cmds.skinCluster(skin, edit=True, addInfluence=jnt, weight=0)

        infs = MSkin.influenceObjects()
        weights_array = om.MDoubleArray(len(infs)*verts_num, 0.0)
        
        for i in range(len(infs)):
            inf = infs[i]
            index = list(infs).index(inf)
            #transfer duplicate weights to weights_array
            if inf not in dup_infs:            
                weights_array[i*len(infs) + index] = 0
            else:
                dup_index = list(dup_infs).index(inf)
                for j in range(verts_num):
                    value = dup_weights[j*len(dup_infs) + dup_index]
                    weights_array[j*len(infs) + index] = value
        mesh_dag = om.MSelectionList().add(self.orig_mesh).getDagPath(0)
        comp_mobj = self.get_mcomp(self.comp)[1] 
        MSkin.setWeights(mesh_dag, comp_mobj, om.MIntArray(list(range(len(infs)))), weights_array)
      
    def local_assign(self):
        # select the verts and joints        
        for obj in self.selection:
            if cmds.objectType(obj)=='joint':
                self.joints.append(obj)
            else:
                self.comp.append(obj)
        #get vertex components
        self.orig_mesh= self.get_mesh_from_comp(self.comp)
        
        #copy skin weight
        self._dup_mesh = cmds.duplicate(self.orig_mesh)[0]
        cmds.skinCluster(self.joints, self._dup_mesh, toSelectedBones=True)
        
        #assign weight        
        self.dup_weight_to_comp()
        
        cmds.delete(self._dup_mesh)
        
        print('Reassign successfully!')
        
    def partial_copy(self):
        # select the vertex and source mesh
        source_mesh = None
        for obj in self.selection:
            if cmds.objectType(obj) == 'transform':
                source_mesh =  obj
            else:
                self.comp.append(obj)
        if source_mesh == None:
            raise ValueError("Source mesh not selected!")
        else:
            self.orig_mesh = self.get_mesh_from_comp(self.comp)
            self._dup_mesh = cmds.duplicate(self.orig_mesh)[0]
            self.copyJointInfluences([source_mesh, self._dup_mesh])
            dup_skin = self.get_skincluster(self._dup_mesh)[0]
            self.joints = cmds.skinCluster(dup_skin, query=True, inf=True)
            
            #assign weight from dup
            self.dup_weight_to_comp()
            
            cmds.delete(self._dup_mesh)
            
            print('Weight copied!')
                      


