# -*- coding: utf-8 -*-

import maya.cmds as cmds
import os

def _null(*args):
    pass

class shelfBase(object):
    '''A simple class to build shelves in maya. Since the build method is empty,
    it should be extended by the derived class to build the necessary shelf elements.
    By default it creates an empty shelf called "customShelf".'''

    def __init__(self, name="customShelf", iconPath=""):
        self.name = name

        self.iconPath = iconPath

        self.labelBackground = (0, 0, 0, 0)
        self.labelColour = (.9, .9, .9)

        self._cleanOldShelf()
        cmds.setParent(self.name)
        # self.build()

    def build(self):
        '''This method should be overwritten in derived classes to actually build the shelf
        elements. Otherwise, nothing is added to the shelf.'''
        pass

    def addButon(
        self,
        label,
        icon="commandButton.png",
        command=_null,
        annotation_str=u''):
        '''Adds a shelf button with the specified label, command, double click command and image.'''
        cmds.setParent(self.name)
        if icon:
            icon = os.path.join(self.iconPath, icon)
        cmds.shelfButton(width=35,
                         height=35,
                         image=icon,
                         image1=icon,
                         enableBackground=0,
                         l=label,
                         command=command,
                         style='iconOnly',
                         imageOverlayLabel=label,
                         overlayLabelBackColor=self.labelBackground,
                         overlayLabelColor=self.labelColour,
                         annotation=annotation_str)

    def addMenuItem(self, parent, label, command=_null, icon=""):
        '''Adds a shelf button with the specified label, command, double click command and image.'''
        if icon:
            icon = os.path.join(self.iconPath, icon)
        return cmds.menuItem(p=parent,
                             l=label,
                             c=command,
                             image="")

    def addSubMenu(self, parent, label, icon=None):
        '''Adds a sub menu item with the specified label and icon to the specified parent popup menu.'''
        if icon:
            icon = os.path.join(self.iconPath, icon)
        return cmds.menuItem(p=parent,
                             l=label,
                             i=icon,
                             subMenu=True)

    def addText(self, label, bg_color=(0.1, 0.1, 0.1)):
        '''Adds a shelf Text with the specified label.'''
        cmds.setParent(self.name)
        cmds.text(l=label,
                  width=60,
                  height=35,
                  align='center',
                  backgroundColor=bg_color)

    def addSeparator(self):
        cmds.setParent(self.name)
        cmds.separator(width=20,
                       height=35,
                       manage=1,
                       style="single")

    def _cleanOldShelf(self):
        '''Checks if the shelf exists and empties it if it does or creates it if it does not.'''
        if cmds.shelfLayout(self.name, ex=True):
            if cmds.shelfLayout(self.name, q=True, childArray=True):
                for each in cmds.shelfLayout(
                        self.name, q=True, childArray=True):
                    cmds.deleteUI(each)
        else:
            cmds.shelfLayout(self.name, p="ShelfLayout")
