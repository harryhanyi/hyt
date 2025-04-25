import sys
import inspect
from imp import reload

import maya.cmds as cmds
import maya.api.OpenMaya as om
import maya.OpenMayaUI as omui

from PySide2 import QtWidgets
import shiboken2

import nsrigProximityMapUtils as utils
reload(utils)


#Global variables
_nsrigProximityMapTargetWidgetInstance = None


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

class TargetData( object ):
    def __init__( self ):
        self.id = -1
        self.envelope = 1.0
        self.radiusMult = 1.0
        self.geometry = None  # to be MDagPath instance when initialized 
    
    def isValid( self ):
        return self.id >= 0
    
    def __eq__( self, other ):
        if isinstance( other, TargetData):
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


class TargetHeader(BaseWidget):
    """
    BaseUIElem-->BaseWidget-->this
    """
    PREFIX = "nsrigProximityMapTarget"
    LAYOUT_NAME = "%sHeaderLayout" % PREFIX
        
    def __init__(self, node, attr, name=None, parent=None, parentWidget=None):
        super(TargetHeader, self).__init__(node, attr, name, parent, parentWidget)
        self._create()
        self.refresh()
    
    def _createWidgets(self):
        self.btnAddTarget = cmds.button('%sAddTargetBtn' % self.PREFIX, l='Add')
        self.btnRemoveTarget = cmds.button("%sRemoveTargetBtn" % self.PREFIX, l='Remove')
        cmds.setParent("..")  # end of self._layout
        
        cmds.formLayout(self._layout, e=1, 
                        af=[(self.btnAddTarget, 'left', 0),
                            (self.btnRemoveTarget, 'right', 0)
                           ],
                        ap=[(self.btnAddTarget, 'right', 0, 50),
                            (self.btnRemoveTarget, 'left', 0, 50),
                           ]
                        )
    
    def _setupCmds(self):
        super(TargetHeader, self)._setupCmds()

        cmdFunc = self._cmdAddTarget
        cmds.button(self.btnAddTarget, e=1, c=cmdFunc)

        cmdFunc = self._cmdRemoveTarget
        cmds.button(self.btnRemoveTarget, e=1, c=cmdFunc)
        
    def _cmdAddTarget(self, *args):
        sels = cmds.ls(sl=1)
        if not sels:
            om.MGlobal.displayError("Please select some meshes first.")
            return

        for sel in sels:
            utils.addTarget(self._node, sel)

        selector = self._parentWidget.selector()
        selector.refresh()
    
    def _cmdRemoveTarget(self, *args):
        target = self._parentWidget.selector().lastSelectedTarget()

        if not target:
            om.MGlobal.displayError("Please select target item from list below.")
            return

        utils.removeTarget(self._node, target.id)

        selector = self._parentWidget.selector()
        selector.refresh()


class TargetSelector(BaseWidget):
    """
    BaseUIElem-->BaseWidget-->this
    """
    PREFIX = "nsrigProximityMapTarget"
    LAYOUT_NAME = "%sSelectorLayout" % PREFIX
    
    def __init__(self, node, attr, name=None, parent=None, parentWidget=None):
        super(TargetSelector, self).__init__(node, attr, name, parent, parentWidget)
        self.targets = []
        self._prevSelectedItem = None
        self._create()
        self.refresh()
    
    def _createWidgets(self):
        self._path = cmds.treeView("%sView" % self.PREFIX, p=self._layout,
                                   nb=1, ams=1, h=180)

        self._contexMenu = cmds.popupMenu( "%sCtxMenu" % self.PREFIX, p=self._path)
        self.menuRefresh = cmds.menuItem("%sRefreshMenu" % self.PREFIX, l="Refresh")
        cmds.menuItem( divider=1 )
        
        self.menuSelAll = cmds.menuItem("%sSelectAllMenu" % self.PREFIX, l="Select all")
        cmds.menuItem( divider=1 )
        
        # TODO - multi selectable, editable widget, support maya sets, like collider widget in flesh widget
        cmds.setParent("..")
        
        cmds.formLayout(self._layout, e=1, 
                        af=[(self._path, 'left', 0),
                            (self._path, 'right', 0)
                           ],
                        )
    
    def _setupCmds(self):
        super(TargetSelector, self)._setupCmds()

        cmdFunc = lambda *args: self.refresh()
        cmds.menuItem(self.menuRefresh, e=1, c=cmdFunc)
        
        cmdFunc = lambda *args: self._cmdSelect()
        cmds.treeView(self._path, e=1, idc=cmdFunc)
         
        cmdFunc = lambda *args: self._cmdSelectAll()
        cmds.menuItem(self.menuSelAll, e=1, c=cmdFunc)
        
        cmdFunc = self._cmdLastSelectedItemIndex
        cmds.treeView(self._path, e=1, sc=cmdFunc)
    
    def _initData(self):
        del self.targets[:]
        
        rootAttr = "%s.%s" % (self._node, self._attr)
        logIds = cmds.getAttr(rootAttr, mi=1)
        
        if not logIds: return

        for id in logIds:
            d = TargetData()
            d.id = id
            d.envelope = cmds.getAttr('%s[%d].targetEnvelope' % (rootAttr, id))
            d.radiusMult = cmds.getAttr('%s[%d].targetRadiusMult' % (rootAttr, id))

            hist = cmds.listConnections("%s[%d].targetGeometry" % (rootAttr, id), s=1, d=0)
            if hist:
                d.geometry = getDagPath(hist[0])

            self.targets.append(d)
    
    def _cmdLastSelectedItemIndex(self, *args):
        selectedItems = cmds.treeView(self._path, q=1, si=1)
        if selectedItems and len(selectedItems)==1:
            # print(selectedItems)
            for item in selectedItems:
                cmds.treeView(self._path, e=1, si=[item, False])

        cmds.treeView(self._path, e=1, si=[args[0], True])
        self._prevSelectedItem = args[0]
        
        self._parentWidget.option().refresh()
        
    def _cmdSelect(self):
        selectedItems = cmds.treeView(self._path, q=1, si=1)
        toBeSelected = []
        try:
            for item in selectedItems:
                itemId = cmds.treeView(self._path, q=1, idx=item)
                target = self.targets[itemId]
                if target.geometry:
                    toBeSelected.append( target.geometry.partialPathName() )
            
            cmds.select( toBeSelected )
        except: pass
        
    def _cmdSelectAll(self):
        toBeSelected = []
        for target in self.targets:
            if target.geometry.isValid():
                toBeSelected.append( target.geometry.partialPathName() )
        
        if toBeSelected: cmds.select( toBeSelected )

    # Public interface
    def refresh(self):
        self._initData()
        
        cmds.treeView(self._path, e=1, ra=1)
        
        for target in self.targets:
            # itemName = "[%d] %s" % (target.id, target.name)
            itemName = target.geometry.partialPathName()

            cmds.treeView(self._path, e=1, ai=(itemName, ""))

            cmds.treeView(self._path, e=1, eb=[itemName, 1, 0])
            cmds.treeView(self._path, e=1, btc=[itemName, 1, 0.18, 0.18, 0.18])
            cmds.treeView(self._path, e=1, bti=[itemName, 1, '[%d]' % target.id])
            cmds.treeView(self._path, e=1, btp=[itemName, 1, 'target index'])
        
        if self._prevSelectedItem:
            try:
                cmds.treeView(self._path, e=1, si=[self._prevSelectedItem, True])
            except:
                pass
    
    def lastSelectedTarget( self ):        
        selectedItems = cmds.treeView(self._path, q=1, si=1)
        if not selectedItems: return None
        # print( selectedItems )

        itemId = cmds.treeView(self._path, q=1, idx=selectedItems[-1])

        if not self.targets: self.refresh()
        target = self.targets[itemId]

        if not target.isValid(): self.refresh()
        target = self.targets[itemId]

        return target
    
    def setNode(self, node):
        self._node = node
        self._prevSelectedItem = None
        self.refresh()


class TargetOption(BaseWidget):
    """
    BaseUIElem-->BaseWidget-->this
    """
    
    PREFIX = "nsrigProximityMapTarget"
    LAYOUT_NAME = "%sOptionLayout" % PREFIX
    
    def __init__(self, node, attr, name=None, parent=None, parentWidget=None):
        super(TargetOption, self).__init__(node, attr, name, parent, parentWidget)
        self._create()
        self.refresh()
    
    def _createWidgets(self):
        colLayout = cmds.columnLayout()

        self.sldTargetEnvelope = cmds.floatSliderGrp("%sEnvelopeSlider" % self.PREFIX,
                                                     min=0, max=1, fmn=0, fmx=1, v=1,
                                                     l="Target Envelope")

        self.sldTargetRadiusMult = cmds.floatSliderGrp("%sRadiusMultSlider" % self.PREFIX,
                                                       min=0, max=5, fmn=0, fmx=20, v=1,
                                                       l="Target Radius Mult")

        cmds.setParent("..") # end of column layout
        cmds.setParent("..")  # end of self._layout

        cmds.formLayout(self._layout, e=1, 
                        af=[(colLayout, 'left', 0),
                            (colLayout, 'right', 0)
                           ],
                        )

    def _setupCmds(self):
        super(TargetOption, self)._setupCmds()

    def _currentSelectedTarget(self):
        selector = self._parentWidget.selector()
        return selector.lastSelectedTarget()
         
    # Public interface
    
    def refresh(self):
        #print ("%s.%s" % (self.__class__.__name__, (inspect.stack()[0][3])))

        target = self._currentSelectedTarget()
        if target == None: return
        
        id = target.id

        attr = "%s.%s[%d].%s" % (self._node, self._attr, id, "targetEnvelope")
        self.connectGrpControl(self.sldTargetEnvelope, attr)

        attr = "%s.%s[%d].%s" % (self._node, self._attr, id, "targetRadiusMult")
        self.connectGrpControl(self.sldTargetRadiusMult, attr)
        

class TargetWidget(BaseAttrWidget):
    """
    BaseUIElem-->BaseWidget-->BaseAttrWidget-->this
    """
    
    LAYOUT_NAME = "nsrigProximityMapTargetTopLayout"
    
    def __init__(self, node, attr, name, parent=None, parentWidget=None):
        super(TargetWidget, self).__init__(node, attr, name, parent, parentWidget)
    
    def _createHeader(self):
        self._header = TargetHeader(self._node, self._attr, self._name, self._layout, self)
        return self._header.layout()
        
    def _createSelector(self):
        # return None
        self._selector = TargetSelector(self._node, self._attr, self._name, self._layout, self)
        return self._selector.layout()
         
    def _createOption(self):
        # return None
        self._option = TargetOption(self._node, self._attr, self._name, self._layout, self)
        return self._option.layout()


#--------------------------------------------------------------------------------------
def createTargetWidget(node, attr, name, parent=None, parentWidget=None):
    global _nsrigProximityMapTargetWidgetInstance
    _nsrigProximityMapTargetWidgetInstance = TargetWidget(node, attr, name, parent, parentWidget)

def updateTargetWidget(node):
    global _nsrigProximityMapTargetWidgetInstance
    
    if _nsrigProximityMapTargetWidgetInstance:
        _nsrigProximityMapTargetWidgetInstance.setNode(node)
