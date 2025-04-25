import sys
import inspect
from imp import reload
from wsgiref import validate

import maya.cmds as cmds
import maya.api.OpenMaya as om
import maya.OpenMayaUI as omui

from PySide2 import QtWidgets
import shiboken2

import nsrigPoseInterpolatorUtils as utils
reload(utils)


#Global variables
_nsrigPoseInterpolatorSettingWidgetInstance = None
_nsrigPoseInterpolatorPoseWidgetInstance = None


"""
DEBUG 
"""
_debugInfo = False


"""
LIB
"""
def getMayaWindow():
    '''
    Get the maya main window as a QMainWindow instance
    '''
    ptr = omui.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(long(ptr), QtWidgets.QWidget)

def getMayaLayout(layout):
    ptr = omui.MQtUtil.findLayout(layout)
    if ptr is not None:
        return shiboken2.wrapInstance(long(ptr), QtWidgets.QWidget).layout()

def getMayaWidget(layout):
    ptr = omui.MQtUtil.findLayout(layout)
    if ptr is not None:
        return shiboken2.wrapInstance(long(ptr), QtWidgets.QWidget)

def getDependencyNode(name):
    selList = om.MSelectionList()
    
    try:
        selList.add(name)
        return selList.getDependNode(0)
    except:
        return None

def getDagPath(name):
    selList = om.MSelectionList()
    
    try:
        selList.add(name)
        return selList.getDagPath(0)
    except:
        return None

def getShapePath(name):
    path = getDagPath(name)
    
    if path.apiType() == om.MFn.kTransform:
        path.extendToShape()
    return path

def isTransform(name):
    path = getDagPath(name)
    
    return path.apiType() == om.MFn.kTransform

def multiGetNextFreeIndex(node, attr):
    depNode = getDependencyNode(node)
    fnDep = om.MFnDependencyNode(depNode)
    
    attrPlug = fnDep.findPlug(attr)
    indices = om.MIntArray()
    attrPlug.getExistingArrayAttributeIndices(indices)
    if indices.length()==0: return 0
    
    return indices[-1] + 1

def getOptionMenuIndexFromLabel(control, label):
    items = cmds.optionMenu(control, q=1, ill=1)
    for item in items:
        itemLabel = cmds.menuItem(item, q=1, l=1)
        if label == itemLabel:
            return items.index(item) + 1
    
    return -1

"""
FUNCTION
"""

class PoseData( object ):
    def __init__( self ):
        self.id = -1
        self.name = ""
        self.envelope = 1.0
        self.isolated = False
        self.color = om.MColor()
        self.matrixPath = om.MDagPath()
        self.values = om.MFloatArray()
    
    def isValid( self ):
        return self.id >= 0
    
    def __eq__( self, other ):
        if isinstance( other, PoseData):
            return self.id == other.id
        return False
    
    def __ne__( self, other ):
        return not self.__eq__(other)


class BaseUIElem(object):
    
    TYPE = ""
    CMD = ""
    
    def __init__(self, name=None, parent=None):
        """
        Args:
          name(str): name of this widget 
          parent(str): path of parent ui returned by maya
        """
        self._name = name
        self._parent = parent
        #self._curParent = cmds.setParent(q=1)
        self._path = ""
        
        # Vars for debuging
        self._className = self.__class__.__name__
    
    def name(self):
        return self._name
    
    def parent(self):
        return self._parent
    
    def path(self):
        return self._path
    
    def exist(self):
        cmdStr = ('cmds.%s("%s", q=1, ex=1)' % (self.CMD, self._name))
        if _debugInfo:
            func = ".".join([self._className, sys._getframe().f_code.co_name])
            print ("func: " + ", ".join([func, cmdStr]))
        return eval(cmdStr)
    
    def enable(self):
        cmdStr = ('cmds.%s("%s", q=1, en=1)' % (self.CMD, self._name))
        if _debugInfo:
            func = ".".join([self._className, sys._getframe().f_code.co_name])
            print ("func: " + ", ".join([func, cmdStr]))
        return eval(cmdStr)
    
    def setEnable(self, val):
        cmdStr = ('cmds.%s("%s", e=1, en=%s)' % (self.CMD, self._name, val))
        if _debugInfo:
            func = ".".join([self._className, sys._getframe().f_code.co_name])
            print ("func: " + ", ".join([func, cmdStr]))
        eval(cmdStr)
    
    def visible(self):
        cmdStr = ('cmds.%s("%s", q=1, vis=1)' % (self.CMD, self._name))
        if _debugInfo:
            func = ".".join([self._className, sys._getframe().f_code.co_name])
            print ("func: " + ", ".join([func, cmdStr]))
        return eval(cmdStr)
    
    def setVisible(self, val):
        cmdStr = ('cmds.%s("%s", e=1, vis=%s)' % (self.CMD, self._name, val))
        if _debugInfo:
            func = ".".join([self._className, sys._getframe().f_code.co_name])
            print ("func: " + ", ".join([func, cmdStr]))
        eval(cmdStr)
    
    def _create(self):
        NotImplemented


class BaseWidget(BaseUIElem):
    """
    BaseUIElem-->this
    """
    
    LAYOUT_NAME = None
    
    def __init__(self, node, attr, name=None, parent=None, parentWidget=None):
        """
        Args:
          node(str): name of node being attched to this widget
          attr(str): name of attribute being attached to this widget
          name(str): name of this widget 
          parent(str): path of parent ui returned by maya
          parentWidget(str): instance of widget derive from 'BaseUIElem'
        """
        super(BaseWidget, self).__init__(name, parent)
        self._node = node
        self._attr = attr
        self._parentWidget = parentWidget
        self._layout = ""
    
    def layout(self):
        return self._layout
    
    def parentWidget(self):
        return self._parentWidget
    
    def _create(self):
        self._createLayout()
        self._createWidgets()
        self._connectControls()
        self._setupCmds()

    def _createLayout(self):
        if self.LAYOUT_NAME:
            self._layout = cmds.formLayout( self.LAYOUT_NAME )

        if self._layout:
            self._rightClickMenu = cmds.popupMenu( p=self._layout, b=3 )
            self._refreshItem = cmds.menuItem( l="Refresh", p=self._rightClickMenu )
    
    def _createWidgets(self):
        NotImplemented
    
    def _connectControls(self):
        NotImplemented
    
    def _setupCmds(self):
        cmdStr = lambda *args: self.refresh()
        cmds.menuItem( self._refreshItem, e=1, c=cmdStr )
    
    def connectControl(self, control, attr, ids=()):
        if ids:
            for i in ids:
                try:
                    cmds.connectControl(control, attr, index=i)
                except:
                    pass
                    #raise ValueError("Couldn't connect %s to %s at index-%d" % (control, attr, i))
        else:
            cmds.connectControl(control, attr)
    
    def connectGrpControl(self, control, attr):
        self.connectControl( control, attr, (2, 3, 4) )
    
    def connectFldGrpControl(self, control, attr):
        attrIds = (0, 1, 2)
        ctrlIds = (2, 3, 4)
        for ai, ci in zip(attrIds, ctrlIds):
            self.connectControl(control, "%s%d" % (attr, ai), list([ci]))
    
    def refresh(self):
        NotImplemented
    
    def setNode(self, node):
        self._node = node
        self.refresh()


class BaseAttrWidget(BaseWidget):
    """
    BaseUIElem-->BaseWidget-->this
    """
    
    def __init__(self,  node, attr, name=None, parent=None, parentWidget=None):
        super(BaseAttrWidget, self).__init__(node, attr, name, parent, parentWidget)
        self._header = None
        self._selector = None
        self._option = None
        self._create()

    def _createWidgets(self):
        #self._layout.addWidget( self._createHeader() )
        headerLayout = self._createHeader()        
        selectorLayout = self._createSelector()
        optionLayout = self._createOption()
        
        cmds.setParent("..")
        
        cmds.formLayout(self._layout, e=1, 
                        af=[(headerLayout, 'top', 0), 
                            (headerLayout, 'left', 0),
                            (headerLayout, 'right', 0),
                            (selectorLayout, 'left', 0),
                            (selectorLayout, 'right', 0),
                            (optionLayout, 'left', 0),
                            (optionLayout, 'right', 0),
                           ],
                        
                        ac=[
                            (selectorLayout, "top", 2, headerLayout),
                            (optionLayout, "top", 2, selectorLayout),
                           ]
                        )
    
    def _createOption(self):
        NotImplemented
    
    def header(self):
        return self._header
    
    def selector(self):
        return self._selector
    
    def option(self):
        return self._option
    
    def refresh(self):
        #print ("%s.%s" % (__name__, (inspect.stack()[0][3])))
        try:
            #print("reflesh", self._option)
            self._option.refresh()
        except:
            pass
        
        try:
            #print("reflesh", self._selector)
            self._selector.refresh()
        except:
            pass
    
    def setNode(self, node):
        self._node = node

        try:
            self._header.setNode(node)
        except:
            pass
        
        try:
            self._option.setNode(node)
        except:
            pass
        
        try:
            self._selector.setNode(node)
        except:
            pass
        
        self.refresh()


class SettingWidget(BaseWidget):
    """
    BaseUIElem-->BaseWidget-->this
    """
    
    PREFIX = "nsrigPoseInterpolatorSetting"
    LAYOUT_NAME = "nsrigPoseInterpolatorSettingLayout"
    
    def __init__(self, node, attr, name, parent=None, parentWidget=None):
        super(SettingWidget, self).__init__(node, attr, name, parent, parentWidget)
        self._create()
        self.refresh()
    
    def _createWidgets(self):
        colLayout = cmds.columnLayout()
        self.sldEnvelope = cmds.floatSliderGrp("%sEnvelopeSlider" % self.PREFIX,
                                               min=0, max=1, fmn=0, fmx=10, v=1,
                                               l="Envelope")

        self.optMenuInterpSpace = cmds.optionMenuGrp("%sInterpSpaceOptMenu" % self.PREFIX,
                                                     l="Interp Space")
        cmds.menuItem(l="Plane", da=0)
        cmds.menuItem(l="Sphere", da=1)

        self.optMenuPosType = cmds.optionMenuGrp("%sPositionTypeOptMenu" % self.PREFIX,
                                                 l="Position Type" )
        cmds.menuItem(l="Matrix", da=0)
        cmds.menuItem(l="Generic", da=1)

        self.sldIter = cmds.intSliderGrp("%sIterationsSlider" % self.PREFIX,
                                         min=-1, max=200, fmn=-1, fmx=10000, v=-1,
                                         l="Iterations")

        self.sldMaxInf = cmds.intSliderGrp("%sMaxInfluencesSlider" % self.PREFIX,
                                           min=2, max=8, fmn=2, fmx=10000, v=4,
                                           l="Max Influences")

        self.sldGridDiv = cmds.intSliderGrp("%sGridDivisionSlider" % self.PREFIX,
                                            min=3, max=32, fmn=3, fmx=128, v=5,
                                            l="Grid Divisions")

        self.fldDrvMatrix = cmds.textFieldGrp("%sDriverMatrixField" % self.PREFIX,
                                               ed=1, tx="", 
                                               l="Driver Matrix")
        self.menuDrvMatrix = cmds.popupMenu("%sDriverMatrixCtxMenu" % self.PREFIX, p=self.fldDrvMatrix)
        self.menuConnMatrix = cmds.menuItem("%sConnectMatrixMenu" % self.PREFIX, 
                                            l='Connect matrix', 
                                            p=self.menuDrvMatrix)
        self.menuConnWorldMatrix = cmds.menuItem("%sConnectWorldMatrixMenu" % self.PREFIX, 
                                                 l='Connect worldMatrix', 
                                                 p=self.menuDrvMatrix)
        self.menuXConnDriverMatrix = cmds.menuItem("%sDisconnectDriverMatrixMenu" % self.PREFIX, 
                                                 l='Break connection', 
                                                 p=self.menuDrvMatrix)
        
        cmds.setParent("..")

        cmds.setParent("..")   # end of self._layout

        cmds.formLayout(self._layout, e=1, 
                        af=[
                            (colLayout, 'left', 0),
                            (colLayout, 'right', 0),
                           ],
                        )
    
    def _setupCmds(self):
        super(SettingWidget, self)._setupCmds()

        cmdFunc = self._cmdConnectMatrix
        cmds.menuItem(self.menuConnMatrix, e=1, c=cmdFunc)

        cmdFunc = self._cmdConnectWorldMatrix
        cmds.menuItem(self.menuConnWorldMatrix, e=1, c=cmdFunc)

        cmdFunc = self._cmdDisconnectDriverMatrix
        cmds.menuItem(self.menuXConnDriverMatrix, e=1, c=cmdFunc)
    
    def _cmdConnectMatrix(self, *args):
        sel = cmds.ls(sl=1, l=1)
        if not sel:
            om.MGlobal.displayError('Please select a transform first.')
            return
        
        utils.connectDriverMatrix(self._node, sel[-1], False)
        self.refresh()
    
    def _cmdConnectWorldMatrix(self, *args):
        sel = cmds.ls(sl=1, l=1)
        if not sel:
            om.MGlobal.displayError('Please select a transform first.')
            return
        
        utils.connectDriverMatrix(self._node, sel[-1], True)
        self.refresh()
    
    def _cmdDisconnectDriverMatrix(self, *args):       
        utils.disconnectDriverMatrix(self._node)

    def refresh(self):
        attr = "%s.%s" % (self._node, "envelope")
        self.connectGrpControl(self.sldEnvelope, attr)

        attr = "%s.%s" % (self._node, "interpSpace")
        self.connectGrpControl(self.optMenuInterpSpace, attr)

        attr = "%s.%s" % (self._node, "positionType")
        self.connectGrpControl(self.optMenuPosType, attr)
        
        attr = "%s.%s" % (self._node, "iterations")
        self.connectGrpControl(self.sldIter, attr)

        attr = "%s.%s" % (self._node, "maxInfluences")
        self.connectGrpControl(self.sldMaxInf, attr)

        attr = "%s.%s" % (self._node, "gridDivisions")
        self.connectGrpControl(self.sldGridDiv, attr)

        attr = "%s.%s" % (self._node, "driverMatrix")
        self.connectGrpControl(self.fldDrvMatrix, attr)
        hist = cmds.listConnections(attr, s=1, d=0, p=1)
        if hist:
            cmds.textFieldGrp(self.fldDrvMatrix, e=1, tx=hist[0])


class PoseHeader(BaseWidget):
    """
    BaseUIElem-->BaseWidget-->this
    """
    PREFIX = "nsrigPoseInterpolatorPose"
    LAYOUT_NAME = "%sHeaderLayout" % PREFIX
        
    def __init__(self, node, attr, name=None, parent=None, parentWidget=None):
        super(PoseHeader, self).__init__(node, attr, name, parent, parentWidget)
        self._create()
        self.refresh()
    
    def _createWidgets(self):
        self.btnAddPose = cmds.button('%sAddPoseBtn' % self.PREFIX, 
                                      l='Add Pose')
        self.btnRandPoseColor = cmds.button("%sRandomizePoseColorsBtn" % self.PREFIX, 
                                            l='Randomize Pose Colors')
        self.btnTogglePoseIsolated = cmds.button("%sTogglePoseIsolatedBtn" % self.PREFIX, 
                                                 l='Toggle Pose Isolated')
        cmds.setParent("..")  # end of self._layout
        
        cmds.formLayout(self._layout, e=1, 
                        af=[(self.btnAddPose, 'left', 0),
                            (self.btnTogglePoseIsolated, 'right', 0)
                           ],
                        ac=[(self.btnRandPoseColor, "left", 1, self.btnAddPose),
                            (self.btnRandPoseColor, "right", 1, self.btnTogglePoseIsolated),
                            ],
                        ap=[(self.btnAddPose, 'right', 0, 33),
                            (self.btnTogglePoseIsolated, 'left', 0, 67),
                           ]
                        )
    
    def _setupCmds(self):
        super(PoseHeader, self)._setupCmds()

        cmdFunc = self._cmdAddPose
        cmds.button(self.btnAddPose, e=1, c=cmdFunc)
         
        cmdFunc = self._cmdRandomizePoseColors
        cmds.button(self.btnRandPoseColor, e=1, c=cmdFunc)

        cmdFunc = self._cmdTogglePoseIsolated
        cmds.button(self.btnTogglePoseIsolated, e=1, c=cmdFunc)
        
    def _cmdAddPose(self, *args):
        sel = cmds.ls(sl=1)
        if not sel:
            om.MGlobal.displayError("Please select some transforms first.")

        utils.connectPoseMatrices(self._node, sel)

        selector = self._parentWidget.selector()
        selector.refresh()
        
    def _cmdRandomizePoseColors(self, *args):
        utils.randomizeAllPoseColors(self._node)
        selector = self._parentWidget.selector()
        selector.refresh()
    
    def _cmdTogglePoseIsolated(self, *args):
        isIsolated = cmds.getAttr('%s.pose[0].poseIsolated' % self._node)
        isIsolated = not isIsolated  # flip the value

        utils.setAllPoseIsolated(self._node, isIsolated)

        selector = self._parentWidget.selector()
        selector.refresh()


class PoseSelector(BaseWidget):
    """
    BaseUIElem-->BaseWidget-->this
    """
    PREFIX = "nsrigPoseInterpolatorPose"
    LAYOUT_NAME = "%sSelectorLayout" % PREFIX
    
    def __init__(self, node, attr, name=None, parent=None, parentWidget=None):
        super(PoseSelector, self).__init__(node, attr, name, parent, parentWidget)
        self.poses = []
        self._prevSelectedItem = None
        self._create()
        self.refresh()
    
    def _createWidgets(self):
        self._path = cmds.treeView("%sView" % self.PREFIX, p=self._layout,
                                   nb=3, ams=1, h=180)

        self._contexMenu = cmds.popupMenu( "%sCtxMenu" % self.PREFIX, p=self._path)
        self.menuRefresh = cmds.menuItem("%sRefreshMenu" % self.PREFIX, l="Refresh")
        cmds.menuItem( divider=1 )
        
        self.menuSel = cmds.menuItem("%sSelectMenu" % self.PREFIX, l="Select")
        self.menuSelAll = cmds.menuItem("%sSelectAllMenu" % self.PREFIX, l="Select all")
        cmds.menuItem( divider=1 )
        
        self.menuRemove = cmds.menuItem("%sRemoveMenu" % self.PREFIX, l="Remove")

        # TODO - multi selectable, editable widget, support maya sets, like collider widget in flesh widget
        cmds.setParent("..")
        
        cmds.formLayout(self._layout, e=1, 
                        af=[(self._path, 'left', 0),
                            (self._path, 'right', 0)
                           ],
                        )
    
    def _setupCmds(self):
        super(PoseSelector, self)._setupCmds()

        cmdFunc = lambda *args: self.refresh()
        cmds.menuItem(self.menuRefresh, e=1, c=cmdFunc)
        
        cmdFunc = lambda *args: self._cmdSelect()
        cmds.menuItem(self.menuSel, e=1, c=cmdFunc)
         
        cmdFunc = lambda *args: self._cmdSelectAll()
        cmds.menuItem(self.menuSelAll, e=1, c=cmdFunc)
        
        cmdFunc = lambda *args: self._cmdRemove()
        cmds.menuItem(self.menuRemove, e=1, c=cmdFunc)
        
        cmdFunc = self._cmdLastSelectedItemIndex
        cmds.treeView(self._path, e=1, sc=cmdFunc)

        cmdFunc = self._cmdChangePoseName
        cmds.treeView(self._path, e=1, elc=cmdFunc)

        cmdFunc = self._cmdSetPoseIsolated
        cmds.treeView(self._path, e=1, pc=[2, cmdFunc])
    
    def _initData(self):
        del self.poses[:]
        
        rootAttr = "%s.%s" % (self._node, self._attr)
        logIds = cmds.getAttr(rootAttr, mi=1)
        
        if not logIds: return

        for id in logIds:
            d = PoseData()
            d.id = id
            d.name = cmds.getAttr('%s[%d].poseName' % (rootAttr, id))
            d.envelope = cmds.getAttr('%s[%d].poseEnvelope' % (rootAttr, id))
            d.isolated = cmds.getAttr('%s[%d].poseIsolated' % (rootAttr, id))

            c = cmds.getAttr('%s[%d].poseColor' % (rootAttr, id))[0]
            d.color = om.MColor((c[0], c[1], c[2], 1.0))

            hist = cmds.listConnections("%s[%d].poseMatrix" % (rootAttr, id), s=1, d=0)
            if hist:
                d.matrixPath = getDagPath(hist[0])

            self.poses.append(d)
    
    def _uniquePoseName(self, id, name):
        suffixId = 0
        newName = str(name)
        for pose in self.poses:
            if id == pose.id: continue
            
            if newName == pose.name:
                suffixId += 1
                newName = '%s%d' % (name, suffixId)
        
        return newName
    
    def _cmdLastSelectedItemIndex(self, *args):
        selectedItems = cmds.treeView(self._path, q=1, si=1)
        if selectedItems and len(selectedItems)==1:
            # print(selectedItems)
            for item in selectedItems:
                cmds.treeView(self._path, e=1, si=[item, False])

        cmds.treeView(self._path, e=1, si=[args[0], True])
        self._prevSelectedItem = args[0]
        
        self._parentWidget.option().refresh()
    
    def _cmdChangePoseName(self, *args):
        # print(args)

        itemId = cmds.treeView(self._path, q=1, idx=args[0])
        id = self.poses[itemId].id
        newName = self._uniquePoseName(id, args[1])
        utils.setPoseName(self._node, id, newName)
        self._prevSelectedItem = newName

        self.refresh()
    
    def _cmdSetPoseIsolated(self, *args):
        itemId = cmds.treeView(self._path, q=1, idx=args[0])
        pose = self.poses[itemId]
        id = pose.id

        isolated = True if pose.isolated == False else False

        utils.setPoseIsolated(self._node, id, isolated)

        self.refresh()
        
    def _cmdSelect(self):
        selectedItems = cmds.treeView(self._path, q=1, si=1)
        toBeSelected = []
        try:
            for item in selectedItems:
                itemId = cmds.treeView(self._path, q=1, idx=item)
                pose = self.poses[itemId]
                if pose.matrixPath.isValid():
                    toBeSelected.append( pose.matrixPath.partialPathName() )
            
            cmds.select( toBeSelected )
        except: pass
        
    def _cmdSelectAll(self):
        toBeSelected = []
        for pose in self.poses:
            if pose.matrixPath.isValid():
                toBeSelected.append( pose.matrixPath.partialPathName() )
        
        if toBeSelected: cmds.select( toBeSelected )
    
    def _cmdRemove(self):
        selectedItems = cmds.treeView(self._path, q=1, si=1)
        
        for item in selectedItems:
            itemId = cmds.treeView(self._path, q=1, idx=item)
            pose = self.poses[itemId]
            utils.deletePose(self._node, pose.id)

            om.MGlobal.displayInfo('pose[%d]: \'%s\' removed from %s' % (
                pose.id, pose.name, self._node))

        self._prevSelectedItem = None

        self.refresh()

    # Public interface
    def refresh(self):
        self._initData()
        
        cmds.treeView(self._path, e=1, ra=1)
        
        for pose in self.poses:
            # itemName = "[%d] %s" % (pose.id, pose.name)
            itemName = pose.name
            if not itemName:
                itemName = '*NO_NAME'
            itemName = self._uniquePoseName( pose.id, itemName )
            pose.name = itemName

            cmds.treeView(self._path, e=1, ai=(itemName, ""))
            cmds.treeView(self._path, e=1, btc=[itemName, 1, pose.color.r, pose.color.g, pose.color.b])
            cmds.treeView(self._path, e=1, btp=[itemName, 1, 'poseColor'])

            cmds.treeView(self._path, e=1, bti=[itemName, 2, 'i'])
            cmds.treeView(self._path, e=1, btp=[itemName, 2, 'poseIsolated'])
            cmds.treeView(self._path, e=1, bs=[itemName, 2, '2StateButton'])
            if pose.isolated:
                cmds.treeView(self._path, e=1, btc=[itemName, 2, 0.945, 0.945, 0.655])
            else:
                cmds.treeView(self._path, e=1, btc=[itemName, 2, 0.3, 0.3, 0.3])

            cmds.treeView(self._path, e=1, eb=[itemName, 3, 0])
            cmds.treeView(self._path, e=1, btc=[itemName, 3, 0.18, 0.18, 0.18])
            cmds.treeView(self._path, e=1, bti=[itemName, 3, '[%d]' % pose.id])
            cmds.treeView(self._path, e=1, btp=[itemName, 3, 'pose index'])
        
        if self._prevSelectedItem:
            try:
                cmds.treeView(self._path, e=1, si=[self._prevSelectedItem, True])
            except:
                pass
    
    def lastSelectedPose( self ):        
        selectedItems = cmds.treeView(self._path, q=1, si=1)
        if not selectedItems: return None
        # print( selectedItems )

        itemId = cmds.treeView(self._path, q=1, idx=selectedItems[-1])

        if not self.poses: self.refresh()
        pose = self.poses[itemId]

        if not pose.isValid(): self.refresh()
        pose = self.poses[itemId]

        return pose
    
    def setNode(self, node):
        self._node = node
        self._prevSelectedItem = None
        self.refresh()


class PoseOption(BaseWidget):
    """
    BaseUIElem-->BaseWidget-->this
    """
    
    PREFIX = "nsrigPoseInterpolatorPose"
    LAYOUT_NAME = "%sOptionLayout" % PREFIX
    
    def __init__(self, node, attr, name=None, parent=None, parentWidget=None):
        super(PoseOption, self).__init__(node, attr, name, parent, parentWidget)
        self._create()
        self.refresh()
    
    def _createWidgets(self):
        colLayout = cmds.columnLayout()

        self.sldPoseEnvelope = cmds.floatSliderGrp("%sEnvelopeSlider" % self.PREFIX,
                                               min=0, max=1, fmn=0, fmx=10, v=1,
                                               l="Pose Envelope")

        self.fldPoseMatrix = cmds.textFieldGrp("%sMatrixField" % self.PREFIX,
                                               ed=1, tx="", 
                                               l="Pose Matrix")
        self.menuPoseMatrix = cmds.popupMenu("%sMatrixCtxMenu" % self.PREFIX, p=self.fldPoseMatrix)
        self.menuConnMatrix = cmds.menuItem("%sConnectMatrixMenu" % self.PREFIX, 
                                            l='Connect matrix', 
                                            p=self.menuPoseMatrix)
        self.menuConnWorldMatrix = cmds.menuItem("%sConnectWorldMatrixMenu" % self.PREFIX, 
                                                 l='Connect worldMatrix', 
                                                 p=self.menuPoseMatrix)
        self.menuXConnPoseMatrix = cmds.menuItem("%sDisconnectPoseMatrixMenu" % self.PREFIX, 
                                                 l='Break connection', 
                                                 p=self.menuPoseMatrix)

        cmds.separator(h=10, style='in')

        self.chkXfm = cmds.checkBoxGrp("%sTransformCheck" % self.PREFIX,
                                       ncb=3,
                                       labelArray3=['Translate', 'Rotate', 'Scale'],
                                       valueArray3=[True, True, False],
                                       l='Transform')

        self.btnConnXfm = cmds.button( label='Connect Transform(s) to poseValues' )

        cmds.setParent("..") # end of column layout
        cmds.setParent("..")  # end of self._layout

        cmds.formLayout(self._layout, e=1, 
                        af=[(colLayout, 'left', 0),
                            (colLayout, 'right', 0)
                           ],
                        )

    def _setupCmds(self):
        super(PoseOption, self)._setupCmds()

        cmdFunc = self._cmdConnectMatrix
        cmds.menuItem(self.menuConnMatrix, e=1, c=cmdFunc)

        cmdFunc = self._cmdConnectWorldMatrix
        cmds.menuItem(self.menuConnWorldMatrix, e=1, c=cmdFunc)

        cmdFunc = self._cmdDisconnectPoseMatrix
        cmds.menuItem(self.menuXConnPoseMatrix, e=1, c=cmdFunc)

        cmdFunc = self._cmdConnectXfm
        cmds.button(self.btnConnXfm, e=1, c=cmdFunc)
    
    def _cmdConnectMatrix(self, *args):
        pose = self._currentSelectedPose()
        if pose == None:
            om.MGlobal.displayError('Please select a pose from the list.')
            return

        sel = cmds.ls(sl=1, l=1)
        if not sel:
            om.MGlobal.displayError('Please select a transform first.')
            return
        
        utils.connectPoseMatrix(self._node, pose.id, sel[-1], False)
        self.refresh()
    
    def _cmdConnectWorldMatrix(self, *args):
        pose = self._currentSelectedPose()
        
        if pose == None:
            om.MGlobal.displayError('Please select a pose from the list.')
            return

        sel = cmds.ls(sl=1, l=1)
        if not sel:
            om.MGlobal.displayError('Please select a transform first.')
            return
        
        utils.connectPoseMatrix(self._node, pose.id, sel[-1], True)
        self.refresh()
    
    def _cmdDisconnectPoseMatrix(self, *args):
        pose = self._currentSelectedPose()
        
        if pose == None:
            om.MGlobal.displayError('Please select a pose from the list.')
            return
        
        utils.disconnectPoseMatrix(self._node, pose.id)
    
    def _cmdConnectXfm(self, *args):
        pose = self._currentSelectedPose()
        if pose == None:
            om.MGlobal.displayError('Please select a pose from the list.')
            return
        
        sel = cmds.ls(sl=1, l=1)
        if not sel:
            om.MGlobal.displayError('Please select some transforms.')
            return

        translate, rotate, scale = cmds.checkBoxGrp(self.chkXfm, q=1, va3=1)

        validXfm = []
        for xfm in sel:
            try:
                utils.connectPoseTransformValues(
                    self._node, pose.id, xfm, translate, rotate, scale)
                validXfm.append(xfm)
            except:
                pass
        
        if validXfm:
            om.MGlobal.displayInfo('Connection made between %s and %s.pose[%d].poseValues' % (
                str(validXfm), self._node, pose.id))

    def _currentSelectedPose(self):
        selector = self._parentWidget.selector()
        return selector.lastSelectedPose()
         
    # Public interface
    
    def refresh(self):
        #print ("%s.%s" % (self.__class__.__name__, (inspect.stack()[0][3])))

        pose = self._currentSelectedPose()
        if pose == None: return
        
        id = pose.id

        attr = "%s.%s[%d].%s" % (self._node, self._attr, id, "poseEnvelope")
        self.connectGrpControl(self.sldPoseEnvelope, attr)

        attr = "%s.%s[%d].%s" % (self._node, self._attr, id, "poseMatrix")
        self.connectGrpControl(self.fldPoseMatrix, attr)
        hist = cmds.listConnections(attr, s=1, d=0, p=1)
        if hist:
            cmds.textFieldGrp(self.fldPoseMatrix, e=1, tx=hist[0])
        

class PoseWidget(BaseAttrWidget):
    """
    BaseUIElem-->BaseWidget-->BaseAttrWidget-->this
    """
    
    LAYOUT_NAME = "nsrigPoseInterpolatorPoseTopLayout"
    
    def __init__(self, node, attr, name, parent=None, parentWidget=None):
        super(PoseWidget, self).__init__(node, attr, name, parent, parentWidget)
    
    def _createHeader(self):
        self._header = PoseHeader(self._node, self._attr, self._name, self._layout, self)
        return self._header.layout()
        
    def _createSelector(self):
        # return None
        self._selector = PoseSelector(self._node, self._attr, self._name, self._layout, self)
        return self._selector.layout()
         
    def _createOption(self):
        # return None
        self._option = PoseOption(self._node, self._attr, self._name, self._layout, self)
        return self._option.layout()


#--------------------------------------------------------------------------------------
def createSettingWidget(node, attr, name, parent=None, parentWidget=None):
    global _nsrigPoseInterpolatorSettingWidgetInstance
    _nsrigPoseInterpolatorSettingWidgetInstance = SettingWidget(node, attr, name, parent, parentWidget)

def updateSettingWidget(node):
    global _nsrigPoseInterpolatorSettingWidgetInstance
    
    if _nsrigPoseInterpolatorSettingWidgetInstance:
        _nsrigPoseInterpolatorSettingWidgetInstance.setNode(node)

#--------------------------------------------------------------------------------------
def createPoseWidget(node, attr, name, parent=None, parentWidget=None):
    global _nsrigPoseInterpolatorPoseWidgetInstance
    _nsrigPoseInterpolatorPoseWidgetInstance = PoseWidget(node, attr, name, parent, parentWidget)

def updatePoseWidget(node):
    global _nsrigPoseInterpolatorPoseWidgetInstance
    
    if _nsrigPoseInterpolatorPoseWidgetInstance:
        _nsrigPoseInterpolatorPoseWidgetInstance.setNode(node)
