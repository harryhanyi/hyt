import os
import maya.cmds as cmds
from maya import OpenMaya
import maya.mel as mel
import maya.OpenMayaUI as omui
try:
    import pymel.core as pm
except:
    mayaLocation = os.environ['MAYA_LOCATION'] + '/bin/'
    cmd_str = '\"' + mayaLocation + 'mayapy\" -m pip install pymel'
    print('pyMel not Installed. Please install it in the command shell with this command:\n ' + cmd_str)    
import maya.mel as mel
import os
from random import random
from functools import partial
import json

#from PyQt import QDialog
from PySide2 import QtGui, QtCore, QtWidgets
from PySide2.QtWidgets import QDialog
#from pyside2uic import compileUi

# test
from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
###

from datetime import datetime, timedelta

#import meta_motion_match_ui
#from meta_motion_match_ui import Ui_MGMetaMotionMatch
from PySide2.QtCore import QObject

##################################################
# UI
##################################################
class Ui_MGMetaMotionMatch(object):
    def setupUi(self, MGMetaMotionMatch):
        MGMetaMotionMatch.setObjectName("MGMetaMotionMatch")
        MGMetaMotionMatch.resize(500, 500)
        MGMetaMotionMatch.setContextMenuPolicy(QtCore.Qt.DefaultContextMenu)
        self.centralwidget = QtWidgets.QWidget(MGMetaMotionMatch)

        self.centralwidget.setObjectName("centralwidget")
        self.gridLayoutWidget = QWidget(self.centralwidget)
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.gridLayoutWidget.setGeometry(QRect(10, 10, 450, 950))
        self.gridLayout = QGridLayout(self.gridLayoutWidget)
        self.gridLayout.setObjectName("gridLayout")
        self.gridLayout.setContentsMargins(0, 0, 0, 0)

        self.scrollArea = QtWidgets.QScrollArea(self.centralwidget)
        self.scrollArea.setGeometry(QtCore.QRect(0, 10, 500, 500))
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setObjectName("scrollArea")
        
        self.scrollAreaWidgetContents = QtWidgets.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 373, 2032))
        self.scrollAreaWidgetContents.setObjectName("scrollAreaWidgetContents")
        
        self.gridLayout_2 = QtWidgets.QGridLayout(self.scrollAreaWidgetContents)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setSizeConstraint(QtWidgets.QLayout.SetNoConstraint)
        self.gridLayout.setObjectName("gridLayout")

        self.lineEdit_mirror_source = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEdit_mirror_source.setObjectName("lineEdit_mirror_source")
        self.gridLayout.addWidget(self.lineEdit_mirror_source, 1, 1, 1, 1)
        self.lineEdit_mirror_target = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.lineEdit_mirror_target.setObjectName("lineEdit_mirror_target")
        self.gridLayout.addWidget(self.lineEdit_mirror_target, 1, 3, 1, 1)
        self.pushButton_mirror_source_pose = QPushButton(self.gridLayoutWidget)
        self.pushButton_mirror_source_pose.setObjectName("pushButton_mirror_source_pose")
        self.gridLayout.addWidget(self.pushButton_mirror_source_pose, 1, 4, 1, 1)
        #self.pushButton_copy_match_pose = QPushButton(self.gridLayoutWidget)
        #self.pushButton_copy_match_pose.setObjectName("pushButton_copy_match_pose")
        #self.gridLayout.addWidget(self.pushButton_copy_match_pose, 1, 1, 1, 1)
        self.checkBox_mirror_invert = QCheckBox(self.gridLayoutWidget)
        self.checkBox_mirror_invert.setObjectName("checkBox_mirror_invert")
        self.gridLayout.addWidget(self.checkBox_mirror_invert, 1, 5, 1, 1)


        self.lineEdit_mocap_joint_lowerarm_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_lowerarm_r.setObjectName("lineEdit_mocap_joint_lowerarm_r")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_lowerarm_r, 21, 3, 1, 1)
        self.pushButton_add_mocap_root = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_root.setObjectName("pushButton_add_mocap_root")
        self.gridLayout.addWidget(self.pushButton_add_mocap_root, 2, 4, 1, 1)
        self.lineEdit_mocap_joint_spine_05 = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_spine_05.setObjectName("lineEdit_mocap_joint_spine_05")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_spine_05, 8, 3, 1, 1)
        self.lineEdit_mh_joint_upperarm_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_upperarm_r.setReadOnly(True)
        self.lineEdit_mh_joint_upperarm_r.setObjectName("lineEdit_mh_joint_upperarm_r")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_upperarm_r, 20, 1, 1, 1)
        self.lineEdit_mh_joint_head = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_head.setReadOnly(True)
        self.lineEdit_mh_joint_head.setObjectName("lineEdit_mh_joint_head")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_head, 11, 1, 1, 1)
        self.lineEdit_mh_joint_hand_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_hand_l.setReadOnly(True)
        self.lineEdit_mh_joint_hand_l.setObjectName("lineEdit_mh_joint_hand_l")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_hand_l, 17, 1, 1, 1)
        self.label = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 13, 1, 1, 1)
        self.pushButton_add_mocap_spine_04 = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_spine_04.setObjectName("pushButton_add_mocap_spine_04")
        self.gridLayout.addWidget(self.pushButton_add_mocap_spine_04, 7, 4, 1, 1)
        self.pushButton_add_mocap_spine_05 = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_spine_05.setObjectName("pushButton_add_mocap_spine_05")
        self.gridLayout.addWidget(self.pushButton_add_mocap_spine_05, 8, 4, 1, 1)
        self.pushButton_add_mocap_clavicle_l = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_clavicle_l.setObjectName("pushButton_add_mocap_clavicle_l")
        self.gridLayout.addWidget(self.pushButton_add_mocap_clavicle_l, 14, 4, 1, 1)
        self.lineEdit_mocap_joint_hand_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_hand_r.setObjectName("lineEdit_mocap_joint_hand_r")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_hand_r, 22, 3, 1, 1)
        self.pushButton_add_mocap_pelvis = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_pelvis.setObjectName("pushButton_add_mocap_pelvis")
        self.gridLayout.addWidget(self.pushButton_add_mocap_pelvis, 3, 4, 1, 1)
        self.lineEdit_mh_joint_lowerarm_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_lowerarm_l.setReadOnly(True)
        self.lineEdit_mh_joint_lowerarm_l.setObjectName("lineEdit_mh_joint_lowerarm_l")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_lowerarm_l, 16, 1, 1, 1)
        self.lineEdit_mocap_joint_clavicle_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_clavicle_r.setObjectName("lineEdit_mocap_joint_clavicle_r")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_clavicle_r, 19, 3, 1, 1)
        self.lineEdit_mh_joint_hand_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_hand_r.setReadOnly(True)
        self.lineEdit_mh_joint_hand_r.setObjectName("lineEdit_mh_joint_hand_r")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_hand_r, 22, 1, 1, 1)
        self.lineEdit_mh_joint_ring_01_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_ring_01_l.setReadOnly(True)
        self.lineEdit_mh_joint_ring_01_l.setObjectName("lineEdit_mh_joint_ring_01_l")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_ring_01_l, 47, 1, 1, 1)
        self.lineEdit_mh_joint_ring_metacarpal_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_ring_metacarpal_l.setReadOnly(True)
        self.lineEdit_mh_joint_ring_metacarpal_l.setObjectName("lineEdit_mh_joint_ring_metacarpal_l")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_ring_metacarpal_l, 45, 1, 1, 1)
        self.label_5 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_5.setObjectName("label_5")
        self.gridLayout.addWidget(self.label_5, 33, 1, 1, 1)
        self.lineEdit_mh_joint_pinky_01_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_pinky_01_l.setReadOnly(True)
        self.lineEdit_mh_joint_pinky_01_l.setObjectName("lineEdit_mh_joint_pinky_01_l")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_pinky_01_l, 51, 1, 1, 1)
        self.lineEdit_mh_joint_ring_03_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_ring_03_r.setReadOnly(True)
        self.lineEdit_mh_joint_ring_03_r.setObjectName("lineEdit_mh_joint_ring_03_r")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_ring_03_r, 69, 1, 1, 1)
        self.lineEdit_mh_joint_spine_03 = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_spine_03.setReadOnly(True)
        self.lineEdit_mh_joint_spine_03.setObjectName("lineEdit_mh_joint_spine_03")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_spine_03, 6, 1, 1, 1)
        self.lineEdit_mh_joint_spine_02 = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_spine_02.setReadOnly(True)
        self.lineEdit_mh_joint_spine_02.setObjectName("lineEdit_mh_joint_spine_02")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_spine_02, 5, 1, 1, 1)
        self.lineEdit_mh_joint_index_metacarpal_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_index_metacarpal_r.setReadOnly(True)
        self.lineEdit_mh_joint_index_metacarpal_r.setObjectName("lineEdit_mh_joint_index_metacarpal_r")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_index_metacarpal_r, 58, 1, 1, 1)
        self.lineEdit_mh_joint_root = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_root.setReadOnly(True)
        self.lineEdit_mh_joint_root.setObjectName("lineEdit_mh_joint_root")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_root, 2, 1, 1, 1)
        self.lineEdit_mh_joint_spine_01 = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_spine_01.setReadOnly(True)
        self.lineEdit_mh_joint_spine_01.setObjectName("lineEdit_mh_joint_spine_01")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_spine_01, 4, 1, 1, 1)
        self.lineEdit_mh_joint_index_03_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_index_03_l.setReadOnly(True)
        self.lineEdit_mh_joint_index_03_l.setObjectName("lineEdit_mh_joint_index_03_l")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_index_03_l, 40, 1, 1, 1)
        self.lineEdit_mh_joint_pelvis = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_pelvis.setReadOnly(True)
        self.lineEdit_mh_joint_pelvis.setObjectName("lineEdit_mh_joint_pelvis")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_pelvis, 3, 1, 1, 1)
        self.lineEdit_mh_joint_spine_05 = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_spine_05.setReadOnly(True)
        self.lineEdit_mh_joint_spine_05.setObjectName("lineEdit_mh_joint_spine_05")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_spine_05, 8, 1, 1, 1)
        self.lineEdit_mh_joint_spine_04 = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_spine_04.setReadOnly(True)
        self.lineEdit_mh_joint_spine_04.setObjectName("lineEdit_mh_joint_spine_04")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_spine_04, 7, 1, 1, 1)
        self.lineEdit_mh_joint_ring_metacarpal_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_ring_metacarpal_r.setReadOnly(True)
        self.lineEdit_mh_joint_ring_metacarpal_r.setObjectName("lineEdit_mh_joint_ring_metacarpal_r")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_ring_metacarpal_r, 66, 1, 1, 1)
        self.lineEdit_mh_joint_middle_metacarpal_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_middle_metacarpal_r.setReadOnly(True)
        self.lineEdit_mh_joint_middle_metacarpal_r.setObjectName("lineEdit_mh_joint_middle_metacarpal_r")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_middle_metacarpal_r, 62, 1, 1, 1)
        self.lineEdit_mh_joint_pinky_02_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_pinky_02_r.setReadOnly(True)
        self.lineEdit_mh_joint_pinky_02_r.setObjectName("lineEdit_mh_joint_pinky_02_r")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_pinky_02_r, 72, 1, 1, 1)
        self.lineEdit_mh_joint_middle_01_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_middle_01_l.setReadOnly(True)
        self.lineEdit_mh_joint_middle_01_l.setObjectName("lineEdit_mh_joint_middle_01_l")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_middle_01_l, 42, 1, 1, 1)
        self.label_6 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_6.setObjectName("label_6")
        self.gridLayout.addWidget(self.label_6, 54, 1, 1, 1)
        self.lineEdit_mh_joint_middle_02_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_middle_02_l.setReadOnly(True)
        self.lineEdit_mh_joint_middle_02_l.setObjectName("lineEdit_mh_joint_middle_02_l")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_middle_02_l, 43, 1, 1, 1)
        self.pushButton_add_mocap_neck_02 = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_neck_02.setObjectName("pushButton_add_mocap_neck_02")
        self.gridLayout.addWidget(self.pushButton_add_mocap_neck_02, 10, 4, 1, 1)
        self.pushButton_add_mocap_neck_01 = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_neck_01.setObjectName("pushButton_add_mocap_neck_01")
        self.gridLayout.addWidget(self.pushButton_add_mocap_neck_01, 9, 4, 1, 1)
        self.pushButton_load_match_file = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_load_match_file.setObjectName("pushButton_load_match_file")
        self.gridLayout.addWidget(self.pushButton_load_match_file, 0, 1, 1, 1)
        self.pushButton_add_mocap_hand_l = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_hand_l.setObjectName("pushButton_add_mocap_hand_l")
        self.gridLayout.addWidget(self.pushButton_add_mocap_hand_l, 17, 4, 1, 1)
        self.pushButton_add_mocap_calf_r = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_calf_r.setObjectName("pushButton_add_mocap_calf_r")
        self.gridLayout.addWidget(self.pushButton_add_mocap_calf_r, 30, 4, 1, 1)
        #self.label_target = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        #self.label_target.setObjectName("label_target")
        #self.gridLayout.addWidget(self.label_target, 2, 3, 1, 1)
        self.pushButton_save_match_file = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_save_match_file.setObjectName("pushButton_save_match_file")
        self.gridLayout.addWidget(self.pushButton_save_match_file, 0, 3, 1, 1)
        self.lineEdit_mocap_joint_pelvis = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_pelvis.setObjectName("lineEdit_mocap_joint_pelvis")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_pelvis, 3, 3, 1, 1)
        self.pushButton_add_mocap_foot_r = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_foot_r.setObjectName("pushButton_add_mocap_foot_r")
        self.gridLayout.addWidget(self.pushButton_add_mocap_foot_r, 31, 4, 1, 1)
        self.pushButton_apply_mocap = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_apply_mocap.setObjectName("pushButton_apply_mocap")
        self.gridLayout.addWidget(self.pushButton_apply_mocap, 0, 4, 1, 1)
        self.pushButton_add_mocap_hand_r = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_hand_r.setObjectName("pushButton_add_mocap_hand_r")
        self.gridLayout.addWidget(self.pushButton_add_mocap_hand_r, 22, 4, 1, 1)
        self.lineEdit_mocap_joint_ball_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_ball_r.setObjectName("lineEdit_mocap_joint_ball_r")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_ball_r, 32, 3, 1, 1)
        self.pushButton_add_mocap_spine_01 = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_spine_01.setObjectName("pushButton_add_mocap_spine_01")
        self.gridLayout.addWidget(self.pushButton_add_mocap_spine_01, 4, 4, 1, 1)
        #self.label_source = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        #self.label_source.setObjectName("label_source")
        #self.gridLayout.addWidget(self.label_source, 2, 1, 1, 1)
        self.lineEdit_mh_joint_pinky_01_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_pinky_01_r.setReadOnly(True)
        self.lineEdit_mh_joint_pinky_01_r.setObjectName("lineEdit_mh_joint_pinky_01_r")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_pinky_01_r, 71, 1, 1, 1)
        self.lineEdit_mh_joint_pinky_02_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_pinky_02_l.setReadOnly(True)
        self.lineEdit_mh_joint_pinky_02_l.setObjectName("lineEdit_mh_joint_pinky_02_l")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_pinky_02_l, 52, 1, 1, 1)
        self.lineEdit_mh_joint_index_02_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_index_02_r.setReadOnly(True)
        self.lineEdit_mh_joint_index_02_r.setObjectName("lineEdit_mh_joint_index_02_r")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_index_02_r, 60, 1, 1, 1)
        self.lineEdit_mh_joint_middle_metacarpal_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_middle_metacarpal_l.setReadOnly(True)
        self.lineEdit_mh_joint_middle_metacarpal_l.setObjectName("lineEdit_mh_joint_middle_metacarpal_l")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_middle_metacarpal_l, 41, 1, 1, 1)
        self.lineEdit_mh_joint_ring_02_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_ring_02_l.setReadOnly(True)
        self.lineEdit_mh_joint_ring_02_l.setObjectName("lineEdit_mh_joint_ring_02_l")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_ring_02_l, 48, 1, 1, 1)
        self.lineEdit_mh_joint_thumb_03_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_thumb_03_l.setReadOnly(True)
        self.lineEdit_mh_joint_thumb_03_l.setObjectName("lineEdit_mh_joint_thumb_03_l")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_thumb_03_l, 36, 1, 1, 1)
        self.lineEdit_mh_joint_neck_01 = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_neck_01.setReadOnly(True)
        self.lineEdit_mh_joint_neck_01.setObjectName("lineEdit_mh_joint_neck_01")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_neck_01, 9, 1, 1, 1)
        self.lineEdit_mh_joint_index_02_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_index_02_l.setReadOnly(True)
        self.lineEdit_mh_joint_index_02_l.setObjectName("lineEdit_mh_joint_index_02_l")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_index_02_l, 39, 1, 1, 1)
        self.lineEdit_mh_joint_foot_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_foot_l.setReadOnly(True)
        self.lineEdit_mh_joint_foot_l.setObjectName("lineEdit_mh_joint_foot_l")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_foot_l, 26, 1, 1, 1)
        self.lineEdit_mh_joint_foot_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_foot_r.setReadOnly(True)
        self.lineEdit_mh_joint_foot_r.setObjectName("lineEdit_mh_joint_foot_r")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_foot_r, 31, 1, 1, 1)
        self.lineEdit_mh_joint_calf_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_calf_r.setReadOnly(True)
        self.lineEdit_mh_joint_calf_r.setObjectName("lineEdit_mh_joint_calf_r")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_calf_r, 30, 1, 1, 1)
        self.lineEdit_mocap_joint_spine_02 = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_spine_02.setObjectName("lineEdit_mocap_joint_spine_02")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_spine_02, 5, 3, 1, 1)
        self.lineEdit_mocap_joint_ball_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_ball_l.setObjectName("lineEdit_mocap_joint_ball_l")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_ball_l, 27, 3, 1, 1)
        self.pushButton_add_mocap_upperarm_r = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_upperarm_r.setObjectName("pushButton_add_mocap_upperarm_r")
        self.gridLayout.addWidget(self.pushButton_add_mocap_upperarm_r, 20, 4, 1, 1)
        self.lineEdit_mh_joint_ball_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_ball_r.setReadOnly(True)
        self.lineEdit_mh_joint_ball_r.setObjectName("lineEdit_mh_joint_ball_r")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_ball_r, 32, 1, 1, 1)
        self.lineEdit_mocap_joint_head = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_head.setObjectName("lineEdit_mocap_joint_head")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_head, 11, 3, 1, 1)
        self.lineEdit_mh_joint_calf_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_calf_l.setReadOnly(True)
        self.lineEdit_mh_joint_calf_l.setObjectName("lineEdit_mh_joint_calf_l")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_calf_l, 25, 1, 1, 1)
        self.lineEdit_mh_joint_thigh_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_thigh_l.setReadOnly(True)
        self.lineEdit_mh_joint_thigh_l.setObjectName("lineEdit_mh_joint_thigh_l")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_thigh_l, 24, 1, 1, 1)
        self.lineEdit_mocap_joint_clavicle_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_clavicle_l.setObjectName("lineEdit_mocap_joint_clavicle_l")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_clavicle_l, 14, 3, 1, 1)
        self.lineEdit_mocap_joint_spine_04 = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_spine_04.setObjectName("lineEdit_mocap_joint_spine_04")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_spine_04, 7, 3, 1, 1)
        self.lineEdit_mh_joint_ball_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_ball_l.setReadOnly(True)
        self.lineEdit_mh_joint_ball_l.setObjectName("lineEdit_mh_joint_ball_l")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_ball_l, 27, 1, 1, 1)
        self.pushButton_add_mocap_lowerarm_r = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_lowerarm_r.setObjectName("pushButton_add_mocap_lowerarm_r")
        self.gridLayout.addWidget(self.pushButton_add_mocap_lowerarm_r, 21, 4, 1, 1)
        self.lineEdit_mocap_joint_hand_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_hand_l.setObjectName("lineEdit_mocap_joint_hand_l")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_hand_l, 17, 3, 1, 1)
        self.lineEdit_mocap_joint_neck_02 = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_neck_02.setObjectName("lineEdit_mocap_joint_neck_02")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_neck_02, 10, 3, 1, 1)
        self.lineEdit_mh_joint_neck_02 = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_neck_02.setReadOnly(True)
        self.lineEdit_mh_joint_neck_02.setObjectName("lineEdit_mh_joint_neck_02")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_neck_02, 10, 1, 1, 1)
        self.pushButton_add_mocap_thigh_l = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_thigh_l.setObjectName("pushButton_add_mocap_thigh_l")
        self.gridLayout.addWidget(self.pushButton_add_mocap_thigh_l, 24, 4, 1, 1)
        self.lineEdit_mocap_joint_thigh_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_thigh_l.setObjectName("lineEdit_mocap_joint_thigh_l")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_thigh_l, 24, 3, 1, 1)
        self.lineEdit_mocap_joint_thigh_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_thigh_r.setObjectName("lineEdit_mocap_joint_thigh_r")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_thigh_r, 29, 3, 1, 1)
        self.lineEdit_mocap_joint_lowerarm_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_lowerarm_l.setObjectName("lineEdit_mocap_joint_lowerarm_l")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_lowerarm_l, 16, 3, 1, 1)
        self.lineEdit_mh_joint_index_metacarpal_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_index_metacarpal_l.setReadOnly(True)
        self.lineEdit_mh_joint_index_metacarpal_l.setObjectName("lineEdit_mh_joint_index_metacarpal_l")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_index_metacarpal_l, 37, 1, 1, 1)
        self.pushButton_add_mocap_head = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_head.setObjectName("pushButton_add_mocap_head")
        self.gridLayout.addWidget(self.pushButton_add_mocap_head, 11, 4, 1, 1)
        self.lineEdit_mocap_joint_foot_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_foot_l.setObjectName("lineEdit_mocap_joint_foot_l")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_foot_l, 26, 3, 1, 1)
        self.pushButton_add_mocap_thigh_r = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_thigh_r.setObjectName("pushButton_add_mocap_thigh_r")
        self.gridLayout.addWidget(self.pushButton_add_mocap_thigh_r, 29, 4, 1, 1)
        self.pushButton_add_mocap_clavicle_r = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_clavicle_r.setObjectName("pushButton_add_mocap_clavicle_r")
        self.gridLayout.addWidget(self.pushButton_add_mocap_clavicle_r, 19, 4, 1, 1)
        self.lineEdit_mocap_joint_spine_03 = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_spine_03.setObjectName("lineEdit_mocap_joint_spine_03")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_spine_03, 6, 3, 1, 1)
        self.lineEdit_mocap_joint_foot_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_foot_r.setObjectName("lineEdit_mocap_joint_foot_r")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_foot_r, 31, 3, 1, 1)
        self.lineEdit_mocap_joint_calf_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_calf_l.setObjectName("lineEdit_mocap_joint_calf_l")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_calf_l, 25, 3, 1, 1)
        self.lineEdit_mh_joint_thigh_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_thigh_r.setReadOnly(True)
        self.lineEdit_mh_joint_thigh_r.setObjectName("lineEdit_mh_joint_thigh_r")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_thigh_r, 29, 1, 1, 1)
        self.lineEdit_mocap_joint_spine_01 = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_spine_01.setObjectName("lineEdit_mocap_joint_spine_01")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_spine_01, 4, 3, 1, 1)
        self.lineEdit_mocap_joint_upperarm_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_upperarm_l.setObjectName("lineEdit_mocap_joint_upperarm_l")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_upperarm_l, 15, 3, 1, 1)
        self.pushButton_add_mocap_foot_l = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_foot_l.setObjectName("pushButton_add_mocap_foot_l")
        self.gridLayout.addWidget(self.pushButton_add_mocap_foot_l, 26, 4, 1, 1)
        self.lineEdit_mh_joint_middle_02_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_middle_02_r.setReadOnly(True)
        self.lineEdit_mh_joint_middle_02_r.setObjectName("lineEdit_mh_joint_middle_02_r")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_middle_02_r, 64, 1, 1, 1)
        self.lineEdit_mh_joint_thumb_02_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_thumb_02_r.setReadOnly(True)
        self.lineEdit_mh_joint_thumb_02_r.setObjectName("lineEdit_mh_joint_thumb_02_r")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_thumb_02_r, 56, 1, 1, 1)
        self.lineEdit_mh_joint_middle_01_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_middle_01_r.setReadOnly(True)
        self.lineEdit_mh_joint_middle_01_r.setObjectName("lineEdit_mh_joint_middle_01_r")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_middle_01_r, 63, 1, 1, 1)
        self.pushButton_add_mocap_ball_r = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_ball_r.setObjectName("pushButton_add_mocap_ball_r")
        self.gridLayout.addWidget(self.pushButton_add_mocap_ball_r, 32, 4, 1, 1)
        self.pushButton_add_mocap_spine_02 = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_spine_02.setObjectName("pushButton_add_mocap_spine_02")
        self.gridLayout.addWidget(self.pushButton_add_mocap_spine_02, 5, 4, 1, 1)
        self.pushButton_add_mocap_calf_l = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_calf_l.setObjectName("pushButton_add_mocap_calf_l")
        self.gridLayout.addWidget(self.pushButton_add_mocap_calf_l, 25, 4, 1, 1)
        self.lineEdit_mh_joint_clavicle_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_clavicle_r.setReadOnly(True)
        self.lineEdit_mh_joint_clavicle_r.setObjectName("lineEdit_mh_joint_clavicle_r")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_clavicle_r, 19, 1, 1, 1)
        self.pushButton_add_mocap_spine_03 = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_spine_03.setObjectName("pushButton_add_mocap_spine_03")
        self.gridLayout.addWidget(self.pushButton_add_mocap_spine_03, 6, 4, 1, 1)
        self.lineEdit_mocap_joint_neck_01 = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_neck_01.setObjectName("lineEdit_mocap_joint_neck_01")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_neck_01, 9, 3, 1, 1)
        self.label_2 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_2.setObjectName("label_2")
        self.gridLayout.addWidget(self.label_2, 18, 1, 1, 1)
        self.pushButton_add_mocap_upperarm_l = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_upperarm_l.setObjectName("pushButton_add_mocap_upperarm_l")
        self.gridLayout.addWidget(self.pushButton_add_mocap_upperarm_l, 15, 4, 1, 1)
        self.lineEdit_mocap_joint_upperarm_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_upperarm_r.setObjectName("lineEdit_mocap_joint_upperarm_r")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_upperarm_r, 20, 3, 1, 1)
        self.label_4 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_4.setObjectName("label_4")
        self.gridLayout.addWidget(self.label_4, 28, 1, 1, 1)
        self.lineEdit_mocap_joint_calf_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_calf_r.setObjectName("lineEdit_mocap_joint_calf_r")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_calf_r, 30, 3, 1, 1)
        self.lineEdit_mh_joint_lowerarm_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_lowerarm_r.setReadOnly(True)
        self.lineEdit_mh_joint_lowerarm_r.setObjectName("lineEdit_mh_joint_lowerarm_r")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_lowerarm_r, 21, 1, 1, 1)
        self.lineEdit_mh_joint_clavicle_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_clavicle_l.setReadOnly(True)
        self.lineEdit_mh_joint_clavicle_l.setObjectName("lineEdit_mh_joint_clavicle_l")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_clavicle_l, 14, 1, 1, 1)
        self.pushButton_add_mocap_lowerarm_l = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_lowerarm_l.setObjectName("pushButton_add_mocap_lowerarm_l")
        self.gridLayout.addWidget(self.pushButton_add_mocap_lowerarm_l, 16, 4, 1, 1)
        self.label_3 = QtWidgets.QLabel(self.scrollAreaWidgetContents)
        self.label_3.setObjectName("label_3")
        self.gridLayout.addWidget(self.label_3, 23, 1, 1, 1)
        self.lineEdit_mh_joint_upperarm_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_upperarm_l.setReadOnly(True)
        self.lineEdit_mh_joint_upperarm_l.setObjectName("lineEdit_mh_joint_upperarm_l")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_upperarm_l, 15, 1, 1, 1)
        self.pushButton_add_mocap_ball_l = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_ball_l.setObjectName("pushButton_add_mocap_ball_l")
        self.gridLayout.addWidget(self.pushButton_add_mocap_ball_l, 27, 4, 1, 1)
        self.lineEdit_mh_joint_pinky_03_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_pinky_03_r.setReadOnly(True)
        self.lineEdit_mh_joint_pinky_03_r.setObjectName("lineEdit_mh_joint_pinky_03_r")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_pinky_03_r, 73, 1, 1, 1)
        self.lineEdit_mh_joint_pinky_metacarpal_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_pinky_metacarpal_l.setReadOnly(True)
        self.lineEdit_mh_joint_pinky_metacarpal_l.setObjectName("lineEdit_mh_joint_pinky_metacarpal_l")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_pinky_metacarpal_l, 50, 1, 1, 1)
        self.lineEdit_mh_joint_index_01_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_index_01_r.setReadOnly(True)
        self.lineEdit_mh_joint_index_01_r.setObjectName("lineEdit_mh_joint_index_01_r")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_index_01_r, 59, 1, 1, 1)
        self.lineEdit_mh_joint_pinky_03_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_pinky_03_l.setReadOnly(True)
        self.lineEdit_mh_joint_pinky_03_l.setObjectName("lineEdit_mh_joint_pinky_03_l")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_pinky_03_l, 53, 1, 1, 1)
        self.lineEdit_mocap_joint_thumb_01_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_thumb_01_l.setObjectName("lineEdit_mocap_joint_thumb_01_l")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_thumb_01_l, 34, 3, 1, 1)
        self.lineEdit_mocap_joint_root = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_root.setObjectName("lineEdit_mocap_joint_root")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_root, 2, 3, 1, 1)
        self.lineEdit_mh_joint_thumb_02_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_thumb_02_l.setReadOnly(True)
        self.lineEdit_mh_joint_thumb_02_l.setObjectName("lineEdit_mh_joint_thumb_02_l")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_thumb_02_l, 35, 1, 1, 1)
        self.lineEdit_mh_joint_thumb_03_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_thumb_03_r.setReadOnly(True)
        self.lineEdit_mh_joint_thumb_03_r.setObjectName("lineEdit_mh_joint_thumb_03_r")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_thumb_03_r, 57, 1, 1, 1)
        self.lineEdit_mh_joint_thumb_01_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_thumb_01_r.setReadOnly(True)
        self.lineEdit_mh_joint_thumb_01_r.setObjectName("lineEdit_mh_joint_thumb_01_r")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_thumb_01_r, 55, 1, 1, 1)
        self.lineEdit_mh_joint_ring_01_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_ring_01_r.setReadOnly(True)
        self.lineEdit_mh_joint_ring_01_r.setObjectName("lineEdit_mh_joint_ring_01_r")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_ring_01_r, 67, 1, 1, 1)
        self.lineEdit_mh_joint_ring_02_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_ring_02_r.setReadOnly(True)
        self.lineEdit_mh_joint_ring_02_r.setObjectName("lineEdit_mh_joint_ring_02_r")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_ring_02_r, 68, 1, 1, 1)
        self.lineEdit_mh_joint_ring_03_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_ring_03_l.setReadOnly(True)
        self.lineEdit_mh_joint_ring_03_l.setObjectName("lineEdit_mh_joint_ring_03_l")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_ring_03_l, 49, 1, 1, 1)
        self.lineEdit_mh_joint_middle_03_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_middle_03_l.setReadOnly(True)
        self.lineEdit_mh_joint_middle_03_l.setObjectName("lineEdit_mh_joint_middle_03_l")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_middle_03_l, 44, 1, 1, 1)
        self.lineEdit_mh_joint_thumb_01_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_thumb_01_l.setReadOnly(True)
        self.lineEdit_mh_joint_thumb_01_l.setObjectName("lineEdit_mh_joint_thumb_01_l")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_thumb_01_l, 34, 1, 1, 1)
        self.lineEdit_mh_joint_middle_03_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_middle_03_r.setReadOnly(True)
        self.lineEdit_mh_joint_middle_03_r.setObjectName("lineEdit_mh_joint_middle_03_r")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_middle_03_r, 65, 1, 1, 1)
        self.lineEdit_mh_joint_index_01_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_index_01_l.setReadOnly(True)
        self.lineEdit_mh_joint_index_01_l.setObjectName("lineEdit_mh_joint_index_01_l")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_index_01_l, 38, 1, 1, 1)
        self.lineEdit_mh_joint_index_03_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_index_03_r.setReadOnly(True)
        self.lineEdit_mh_joint_index_03_r.setObjectName("lineEdit_mh_joint_index_03_r")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_index_03_r, 61, 1, 1, 1)
        self.lineEdit_mh_joint_pinky_metacarpal_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mh_joint_pinky_metacarpal_r.setReadOnly(True)
        self.lineEdit_mh_joint_pinky_metacarpal_r.setObjectName("lineEdit_mh_joint_pinky_metacarpal_r")
        self.gridLayout.addWidget(self.lineEdit_mh_joint_pinky_metacarpal_r, 70, 1, 1, 1)
        self.lineEdit_mocap_joint_thumb_03_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_thumb_03_l.setObjectName("lineEdit_mocap_joint_thumb_03_l")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_thumb_03_l, 36, 3, 1, 1)
        self.lineEdit_mocap_joint_thumb_02_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_thumb_02_l.setObjectName("lineEdit_mocap_joint_thumb_02_l")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_thumb_02_l, 35, 3, 1, 1)
        self.lineEdit_mocap_joint_index_metacarpal_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_index_metacarpal_l.setObjectName("lineEdit_mocap_joint_index_metacarpal_l")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_index_metacarpal_l, 37, 3, 1, 1)
        self.lineEdit_mocap_joint_index_01_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_index_01_l.setObjectName("lineEdit_mocap_joint_index_01_l")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_index_01_l, 38, 3, 1, 1)
        self.lineEdit_mocap_joint_index_02_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_index_02_l.setObjectName("lineEdit_mocap_joint_index_02_l")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_index_02_l, 39, 3, 1, 1)
        self.lineEdit_mocap_joint_index_03_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_index_03_l.setObjectName("lineEdit_mocap_joint_index_03_l")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_index_03_l, 40, 3, 1, 1)
        self.lineEdit_mocap_joint_middle_metacarpal_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_middle_metacarpal_l.setObjectName("lineEdit_mocap_joint_middle_metacarpal_l")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_middle_metacarpal_l, 41, 3, 1, 1)
        self.lineEdit_mocap_joint_middle_01_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_middle_01_l.setObjectName("lineEdit_mocap_joint_middle_01_l")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_middle_01_l, 42, 3, 1, 1)
        self.lineEdit_mocap_joint_middle_02_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_middle_02_l.setObjectName("lineEdit_mocap_joint_middle_02_l")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_middle_02_l, 43, 3, 1, 1)
        self.lineEdit_mocap_joint_middle_03_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_middle_03_l.setObjectName("lineEdit_mocap_joint_middle_03_l")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_middle_03_l, 44, 3, 1, 1)
        self.lineEdit_mocap_joint_ring_metacarpal_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_ring_metacarpal_l.setObjectName("lineEdit_mocap_joint_ring_metacarpal_l")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_ring_metacarpal_l, 45, 3, 1, 1)
        self.lineEdit_mocap_joint_ring_01_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_ring_01_l.setObjectName("lineEdit_mocap_joint_ring_01_l")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_ring_01_l, 47, 3, 1, 1)
        self.lineEdit_mocap_joint_ring_02_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_ring_02_l.setObjectName("lineEdit_mocap_joint_ring_02_l")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_ring_02_l, 48, 3, 1, 1)
        self.lineEdit_mocap_joint_ring_03_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_ring_03_l.setObjectName("lineEdit_mocap_joint_ring_03_l")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_ring_03_l, 49, 3, 1, 1)
        self.lineEdit_mocap_joint_pinky_metacarpal_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_pinky_metacarpal_l.setObjectName("lineEdit_mocap_joint_pinky_metacarpal_l")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_pinky_metacarpal_l, 50, 3, 1, 1)
        self.lineEdit_mocap_joint_pinky_01_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_pinky_01_l.setObjectName("lineEdit_mocap_joint_pinky_01_l")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_pinky_01_l, 51, 3, 1, 1)
        self.lineEdit_mocap_joint_pinky_02_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_pinky_02_l.setObjectName("lineEdit_mocap_joint_pinky_02_l")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_pinky_02_l, 52, 3, 1, 1)
        self.lineEdit_mocap_joint_pinky_03_l = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_pinky_03_l.setObjectName("lineEdit_mocap_joint_pinky_03_l")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_pinky_03_l, 53, 3, 1, 1)
        self.lineEdit_mocap_joint_thumb_01_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_thumb_01_r.setObjectName("lineEdit_mocap_joint_thumb_01_r")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_thumb_01_r, 55, 3, 1, 1)
        self.lineEdit_mocap_joint_thumb_02_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_thumb_02_r.setObjectName("lineEdit_mocap_joint_thumb_02_r")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_thumb_02_r, 56, 3, 1, 1)
        self.lineEdit_mocap_joint_thumb_03_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_thumb_03_r.setObjectName("lineEdit_mocap_joint_thumb_03_r")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_thumb_03_r, 57, 3, 1, 1)
        self.lineEdit_mocap_joint_index_metacarpal_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_index_metacarpal_r.setObjectName("lineEdit_mocap_joint_index_metacarpal_r")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_index_metacarpal_r, 58, 3, 1, 1)
        self.lineEdit_mocap_joint_index_01_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_index_01_r.setObjectName("lineEdit_mocap_joint_index_01_r")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_index_01_r, 59, 3, 1, 1)
        self.lineEdit_mocap_joint_index_02_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_index_02_r.setObjectName("lineEdit_mocap_joint_index_02_r")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_index_02_r, 60, 3, 1, 1)
        self.lineEdit_mocap_joint_index_03_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_index_03_r.setObjectName("lineEdit_mocap_joint_index_03_r")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_index_03_r, 61, 3, 1, 1)
        self.lineEdit_mocap_joint_middle_metacarpal_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_middle_metacarpal_r.setObjectName("lineEdit_mocap_joint_middle_metacarpal_r")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_middle_metacarpal_r, 62, 3, 1, 1)
        self.lineEdit_mocap_joint_middle_01_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_middle_01_r.setObjectName("lineEdit_mocap_joint_middle_01_r")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_middle_01_r, 63, 3, 1, 1)
        self.lineEdit_mocap_joint_middle_02_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_middle_02_r.setObjectName("lineEdit_mocap_joint_middle_02_r")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_middle_02_r, 64, 3, 1, 1)
        self.lineEdit_mocap_joint_middle_03_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_middle_03_r.setObjectName("lineEdit_mocap_joint_middle_03_r")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_middle_03_r, 65, 3, 1, 1)
        self.lineEdit_mocap_joint_ring_metacarpal_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_ring_metacarpal_r.setObjectName("lineEdit_mocap_joint_ring_metacarpal_r")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_ring_metacarpal_r, 66, 3, 1, 1)
        self.lineEdit_mocap_joint_ring_01_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_ring_01_r.setObjectName("lineEdit_mocap_joint_ring_01_r")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_ring_01_r, 67, 3, 1, 1)
        self.lineEdit_mocap_joint_ring_02_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_ring_02_r.setObjectName("lineEdit_mocap_joint_ring_02_r")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_ring_02_r, 68, 3, 1, 1)
        self.lineEdit_mocap_joint_ring_03_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_ring_03_r.setObjectName("lineEdit_mocap_joint_ring_03_r")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_ring_03_r, 69, 3, 1, 1)
        self.lineEdit_mocap_joint_pinky_metacarpal_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_pinky_metacarpal_r.setObjectName("lineEdit_mocap_joint_pinky_metacarpal_r")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_pinky_metacarpal_r, 70, 3, 1, 1)
        self.lineEdit_mocap_joint_pinky_01_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_pinky_01_r.setObjectName("lineEdit_mocap_joint_pinky_01_r")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_pinky_01_r, 71, 3, 1, 1)
        self.lineEdit_mocap_joint_pinky_02_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_pinky_02_r.setObjectName("lineEdit_mocap_joint_pinky_02_r")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_pinky_02_r, 72, 3, 1, 1)
        self.lineEdit_mocap_joint_pinky_03_r = QtWidgets.QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit_mocap_joint_pinky_03_r.setObjectName("lineEdit_mocap_joint_pinky_03_r")
        self.gridLayout.addWidget(self.lineEdit_mocap_joint_pinky_03_r, 73, 3, 1, 1)
        self.pushButton_add_mocap_thumb_01_l = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_thumb_01_l.setObjectName("pushButton_add_mocap_thumb_01_l")
        self.gridLayout.addWidget(self.pushButton_add_mocap_thumb_01_l, 34, 4, 1, 1)
        self.pushButton_add_mocap_thumb_02_l = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_thumb_02_l.setObjectName("pushButton_add_mocap_thumb_02_l")
        self.gridLayout.addWidget(self.pushButton_add_mocap_thumb_02_l, 35, 4, 1, 1)
        self.pushButton_add_mocap_thumb_03_l = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_thumb_03_l.setObjectName("pushButton_add_mocap_thumb_03_l")
        self.gridLayout.addWidget(self.pushButton_add_mocap_thumb_03_l, 36, 4, 1, 1)
        self.pushButton_add_mocap_index_metacarpal_l = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_index_metacarpal_l.setObjectName("pushButton_add_mocap_index_metacarpal_l")
        self.gridLayout.addWidget(self.pushButton_add_mocap_index_metacarpal_l, 37, 4, 1, 1)
        self.pushButton_add_mocap_index_01_l = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_index_01_l.setObjectName("pushButton_add_mocap_index_01_l")
        self.gridLayout.addWidget(self.pushButton_add_mocap_index_01_l, 38, 4, 1, 1)
        self.pushButton_add_mocap_index_02_l = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_index_02_l.setObjectName("pushButton_add_mocap_index_02_l")
        self.gridLayout.addWidget(self.pushButton_add_mocap_index_02_l, 39, 4, 1, 1)
        self.pushButton_add_mocap_index_03_l = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_index_03_l.setObjectName("pushButton_add_mocap_index_03_l")
        self.gridLayout.addWidget(self.pushButton_add_mocap_index_03_l, 40, 4, 1, 1)
        self.pushButton_add_mocap_middle_metacarpal_l = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_middle_metacarpal_l.setObjectName("pushButton_add_mocap_middle_metacarpal_l")
        self.gridLayout.addWidget(self.pushButton_add_mocap_middle_metacarpal_l, 41, 4, 1, 1)
        self.pushButton_add_mocap_middle_01_l = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_middle_01_l.setObjectName("pushButton_add_mocap_middle_01_l")
        self.gridLayout.addWidget(self.pushButton_add_mocap_middle_01_l, 42, 4, 1, 1)
        self.pushButton_add_mocap_middle_02_l = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_middle_02_l.setObjectName("pushButton_add_mocap_middle_02_l")
        self.gridLayout.addWidget(self.pushButton_add_mocap_middle_02_l, 43, 4, 1, 1)
        self.pushButton_add_mocap_middle_03_l = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_middle_03_l.setObjectName("pushButton_add_mocap_middle_03_l")
        self.gridLayout.addWidget(self.pushButton_add_mocap_middle_03_l, 44, 4, 1, 1)
        self.pushButton_add_mocap_ring_metacarpal_l = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_ring_metacarpal_l.setObjectName("pushButton_add_mocap_ring_metacarpal_l")
        self.gridLayout.addWidget(self.pushButton_add_mocap_ring_metacarpal_l, 45, 4, 1, 1)
        self.pushButton_add_mocap_ring_01_l = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_ring_01_l.setObjectName("pushButton_add_mocap_ring_01_l")
        self.gridLayout.addWidget(self.pushButton_add_mocap_ring_01_l, 47, 4, 1, 1)
        self.pushButton_add_mocap_ring_02_l = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_ring_02_l.setObjectName("pushButton_add_mocap_ring_02_l")
        self.gridLayout.addWidget(self.pushButton_add_mocap_ring_02_l, 48, 4, 1, 1)
        self.pushButton_add_mocap_ring_03_l = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_ring_03_l.setObjectName("pushButton_add_mocap_ring_03_l")
        self.gridLayout.addWidget(self.pushButton_add_mocap_ring_03_l, 49, 4, 1, 1)
        self.pushButton_add_mocap_pinky_metacarpal_l = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_pinky_metacarpal_l.setObjectName("pushButton_add_mocap_pinky_metacarpal_l")
        self.gridLayout.addWidget(self.pushButton_add_mocap_pinky_metacarpal_l, 50, 4, 1, 1)
        self.pushButton_add_mocap_pinky_01_l = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_pinky_01_l.setObjectName("pushButton_add_mocap_pinky_01_l")
        self.gridLayout.addWidget(self.pushButton_add_mocap_pinky_01_l, 51, 4, 1, 1)
        self.pushButton_add_mocap_pinky_02_l = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_pinky_02_l.setObjectName("pushButton_add_mocap_pinky_02_l")
        self.gridLayout.addWidget(self.pushButton_add_mocap_pinky_02_l, 52, 4, 1, 1)
        self.pushButton_add_mocap_pinky_03_l = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_pinky_03_l.setObjectName("pushButton_add_mocap_pinky_03_l")
        self.gridLayout.addWidget(self.pushButton_add_mocap_pinky_03_l, 53, 4, 1, 1)
        self.pushButton_add_mocap_thumb_01_r = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_thumb_01_r.setObjectName("pushButton_add_mocap_thumb_01_r")
        self.gridLayout.addWidget(self.pushButton_add_mocap_thumb_01_r, 55, 4, 1, 1)
        self.pushButton_add_mocap_thumb_02_r = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_thumb_02_r.setObjectName("pushButton_add_mocap_thumb_02_r")
        self.gridLayout.addWidget(self.pushButton_add_mocap_thumb_02_r, 56, 4, 1, 1)
        self.pushButton_add_mocap_thumb_03_r = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_thumb_03_r.setObjectName("pushButton_add_mocap_thumb_03_r")
        self.gridLayout.addWidget(self.pushButton_add_mocap_thumb_03_r, 57, 4, 1, 1)
        self.pushButton_add_mocap_index_metacarpal_r = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_index_metacarpal_r.setObjectName("pushButton_add_mocap_index_metacarpal_r")
        self.gridLayout.addWidget(self.pushButton_add_mocap_index_metacarpal_r, 58, 4, 1, 1)
        self.pushButton_add_mocap_index_01_r = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_index_01_r.setObjectName("pushButton_add_mocap_index_01_r")
        self.gridLayout.addWidget(self.pushButton_add_mocap_index_01_r, 59, 4, 1, 1)
        self.pushButton_add_mocap_index_02_r = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_index_02_r.setObjectName("pushButton_add_mocap_index_02_r")
        self.gridLayout.addWidget(self.pushButton_add_mocap_index_02_r, 60, 4, 1, 1)
        self.pushButton_add_mocap_index_03_r = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_index_03_r.setObjectName("pushButton_add_mocap_index_03_r")
        self.gridLayout.addWidget(self.pushButton_add_mocap_index_03_r, 61, 4, 1, 1)
        self.pushButton_add_mocap_middle_metacarpal_r = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_middle_metacarpal_r.setObjectName("pushButton_add_mocap_middle_metacarpal_r")
        self.gridLayout.addWidget(self.pushButton_add_mocap_middle_metacarpal_r, 62, 4, 1, 1)
        self.pushButton_add_mocap_middle_01_r = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_middle_01_r.setObjectName("pushButton_add_mocap_middle_01_r")
        self.gridLayout.addWidget(self.pushButton_add_mocap_middle_01_r, 63, 4, 1, 1)
        self.pushButton_add_mocap_middle_02_r = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_middle_02_r.setObjectName("pushButton_add_mocap_middle_02_r")
        self.gridLayout.addWidget(self.pushButton_add_mocap_middle_02_r, 64, 4, 1, 1)
        self.pushButton_add_mocap_middle_03_r = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_middle_03_r.setObjectName("pushButton_add_mocap_middle_03_r")
        self.gridLayout.addWidget(self.pushButton_add_mocap_middle_03_r, 65, 4, 1, 1)
        self.pushButton_add_mocap_ring_metacarpal_r = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_ring_metacarpal_r.setObjectName("pushButton_add_mocap_ring_metacarpal_r")
        self.gridLayout.addWidget(self.pushButton_add_mocap_ring_metacarpal_r, 66, 4, 1, 1)
        self.pushButton_add_mocap_ring_01_r = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_ring_01_r.setObjectName("pushButton_add_mocap_ring_01_r")
        self.gridLayout.addWidget(self.pushButton_add_mocap_ring_01_r, 67, 4, 1, 1)
        self.pushButton_add_mocap_ring_02_r = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_ring_02_r.setObjectName("pushButton_add_mocap_ring_02_r")
        self.gridLayout.addWidget(self.pushButton_add_mocap_ring_02_r, 68, 4, 1, 1)
        self.pushButton_add_mocap_ring_03_r = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_ring_03_r.setObjectName("pushButton_add_mocap_ring_03_r")
        self.gridLayout.addWidget(self.pushButton_add_mocap_ring_03_r, 69, 4, 1, 1)
        self.pushButton_add_mocap_pinky_metacarpal_r = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_pinky_metacarpal_r.setObjectName("pushButton_add_mocap_pinky_metacarpal_r")
        self.gridLayout.addWidget(self.pushButton_add_mocap_pinky_metacarpal_r, 70, 4, 1, 1)
        self.pushButton_add_mocap_pinky_01_r = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_pinky_01_r.setObjectName("pushButton_add_mocap_pinky_01_r")
        self.gridLayout.addWidget(self.pushButton_add_mocap_pinky_01_r, 71, 4, 1, 1)
        self.pushButton_add_mocap_pinky_02_r = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_pinky_02_r.setObjectName("pushButton_add_mocap_pinky_02_r")
        self.gridLayout.addWidget(self.pushButton_add_mocap_pinky_02_r, 72, 4, 1, 1)
        self.pushButton_add_mocap_pinky_03_r = QtWidgets.QPushButton(self.scrollAreaWidgetContents)
        self.pushButton_add_mocap_pinky_03_r.setObjectName("pushButton_add_mocap_pinky_03_r")
        self.gridLayout.addWidget(self.pushButton_add_mocap_pinky_03_r, 73, 4, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        MGMetaMotionMatch.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MGMetaMotionMatch)
        self.statusbar.setObjectName("statusbar")
        MGMetaMotionMatch.setStatusBar(self.statusbar)

        self.retranslateUi(MGMetaMotionMatch)
        QtCore.QMetaObject.connectSlotsByName(MGMetaMotionMatch)

    def retranslateUi(self, MGMetaMotionMatch):
        MGMetaMotionMatch.setWindowTitle(QtWidgets.QApplication.translate("MGMetaMotionMatch", "MG Metahuman Motion Match", None, -1))
        self.lineEdit_mocap_joint_lowerarm_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_lowerarm_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.pushButton_add_mocap_root.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_root.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.lineEdit_mocap_joint_spine_05.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_spine_05.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mh_joint_upperarm_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_upperarm_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "upperarm_r", None, -1))
        self.lineEdit_mh_joint_head.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_head.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "head", None, -1))
        self.lineEdit_mh_joint_hand_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_hand_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "hand_l", None, -1))
        self.label.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "Left Arm", None, -1))
        self.pushButton_add_mocap_spine_04.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_spine_04.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_spine_05.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_spine_05.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_clavicle_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_clavicle_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.lineEdit_mocap_joint_hand_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_hand_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.pushButton_add_mocap_pelvis.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_pelvis.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.lineEdit_mh_joint_lowerarm_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_lowerarm_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "lowerarm_l", None, -1))
        self.lineEdit_mocap_joint_clavicle_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_clavicle_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mh_joint_hand_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_hand_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "hand_r", None, -1))
        self.lineEdit_mh_joint_ring_01_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_ring_01_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "ring_01_l", None, -1))
        self.lineEdit_mh_joint_ring_metacarpal_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_ring_metacarpal_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "ring_metacarpal_l", None, -1))
        self.label_5.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "Left Hand", None, -1))
        self.lineEdit_mh_joint_pinky_01_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_pinky_01_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "pinky_01_l", None, -1))
        self.lineEdit_mh_joint_ring_03_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_ring_03_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "ring_03_r", None, -1))
        self.lineEdit_mh_joint_spine_03.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_spine_03.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "spine_03", None, -1))
        self.lineEdit_mh_joint_spine_02.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_spine_02.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "spine_02", None, -1))
        self.lineEdit_mh_joint_index_metacarpal_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_index_metacarpal_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "index_metacarpal_r", None, -1))
        self.lineEdit_mh_joint_root.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_root.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "root translation", None, -1))
        self.lineEdit_mh_joint_spine_01.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_spine_01.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "spine_01", None, -1))
        self.lineEdit_mh_joint_index_03_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_index_03_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "index_03_l", None, -1))
        self.lineEdit_mh_joint_pelvis.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_pelvis.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "root rotation", None, -1))
        self.lineEdit_mh_joint_spine_05.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_spine_05.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "spine_05", None, -1))
        self.lineEdit_mh_joint_spine_04.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_spine_04.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "spine_04", None, -1))
        self.lineEdit_mh_joint_ring_metacarpal_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_ring_metacarpal_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "ring_metacarpal_r", None, -1))
        self.lineEdit_mh_joint_middle_metacarpal_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_middle_metacarpal_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "middle_metacarpal_r", None, -1))
        self.lineEdit_mh_joint_pinky_02_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_pinky_02_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "pinky_02_r", None, -1))
        self.lineEdit_mh_joint_middle_01_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_middle_01_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "middle_01_l", None, -1))
        self.label_6.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "Right Hand", None, -1))
        self.lineEdit_mh_joint_middle_02_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_middle_02_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "middle_02_l", None, -1))
        self.pushButton_add_mocap_neck_02.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_neck_02.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_neck_01.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_neck_01.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_load_match_file.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "Load Match File", None, -1))
        self.pushButton_load_match_file.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "Load Match File", None, -1))
        self.pushButton_add_mocap_hand_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_hand_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_calf_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_calf_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        #self.label_target.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "Motion Source Joint", None, -1))
        self.pushButton_save_match_file.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "Save Match File", None, -1))
        self.pushButton_save_match_file.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "Save Match File", None, -1))
        self.lineEdit_mocap_joint_pelvis.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_pelvis.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.pushButton_add_mocap_foot_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_foot_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_apply_mocap.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "Select one source (mocap) and one target object (metahuman) then click Apply Mocap.", None, -1))
        self.pushButton_apply_mocap.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "Apply Mocap", None, -1))
        self.pushButton_add_mocap_hand_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_hand_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.lineEdit_mocap_joint_ball_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_ball_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.pushButton_add_mocap_spine_01.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_spine_01.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        #self.label_source.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "Metahuman Joint", None, -1))
        self.lineEdit_mh_joint_pinky_01_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_pinky_01_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "pinky_01_r", None, -1))
        self.lineEdit_mh_joint_pinky_02_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_pinky_02_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "pinky_02_l", None, -1))
        self.lineEdit_mh_joint_index_02_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_index_02_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "index_02_r", None, -1))
        self.lineEdit_mh_joint_middle_metacarpal_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_middle_metacarpal_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "middle_metacarpal_l", None, -1))
        self.lineEdit_mh_joint_ring_02_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_ring_02_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "ring_02_l", None, -1))
        self.lineEdit_mh_joint_thumb_03_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_thumb_03_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "thumb_03_l", None, -1))
        self.lineEdit_mh_joint_neck_01.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_neck_01.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "neck_01", None, -1))
        self.lineEdit_mh_joint_index_02_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_index_02_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "index_02_l", None, -1))
        self.lineEdit_mh_joint_foot_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_foot_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "foot_l", None, -1))
        self.lineEdit_mh_joint_foot_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_foot_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "foot_r", None, -1))
        self.lineEdit_mh_joint_calf_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_calf_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "calf_r", None, -1))
        self.lineEdit_mocap_joint_spine_02.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_spine_02.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_ball_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_ball_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.pushButton_add_mocap_upperarm_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_upperarm_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.lineEdit_mh_joint_ball_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_ball_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "ball_r", None, -1))
        self.lineEdit_mocap_joint_head.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_head.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mh_joint_calf_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_calf_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "calf_l", None, -1))
        self.lineEdit_mh_joint_thigh_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_thigh_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "thigh_l", None, -1))
        self.lineEdit_mocap_joint_clavicle_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_clavicle_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_spine_04.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_spine_04.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mh_joint_ball_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_ball_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "ball_l", None, -1))
        self.pushButton_add_mocap_lowerarm_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_lowerarm_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.lineEdit_mocap_joint_hand_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_hand_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_neck_02.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_neck_02.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mh_joint_neck_02.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_neck_02.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "neck_02", None, -1))
        self.pushButton_add_mocap_thigh_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_thigh_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.lineEdit_mocap_joint_thigh_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_thigh_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_thigh_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_thigh_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_lowerarm_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_lowerarm_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mh_joint_index_metacarpal_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_index_metacarpal_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "index_metacarpal_l", None, -1))
        self.pushButton_add_mocap_head.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_head.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.lineEdit_mocap_joint_foot_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_foot_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.pushButton_add_mocap_thigh_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_thigh_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_clavicle_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_clavicle_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.lineEdit_mocap_joint_spine_03.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_spine_03.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_foot_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_foot_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_calf_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_calf_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mh_joint_thigh_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_thigh_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "thigh_r", None, -1))
        self.lineEdit_mocap_joint_spine_01.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_spine_01.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_upperarm_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_upperarm_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.pushButton_add_mocap_foot_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_foot_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.lineEdit_mh_joint_middle_02_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_middle_02_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "middle_02_r", None, -1))
        self.lineEdit_mh_joint_thumb_02_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_thumb_02_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "thumb_02_r", None, -1))
        self.lineEdit_mh_joint_middle_01_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_middle_01_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "middle_01_r", None, -1))
        self.pushButton_add_mocap_ball_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_ball_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_spine_02.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_spine_02.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_calf_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_calf_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.lineEdit_mh_joint_clavicle_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_clavicle_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "clavicle_r", None, -1))
        self.pushButton_add_mocap_spine_03.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_spine_03.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.lineEdit_mocap_joint_neck_01.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_neck_01.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.label_2.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "Right Arm", None, -1))
        self.pushButton_add_mocap_upperarm_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_upperarm_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.lineEdit_mocap_joint_upperarm_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_upperarm_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.label_4.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "Right Leg", None, -1))
        self.lineEdit_mocap_joint_calf_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_calf_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mh_joint_lowerarm_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_lowerarm_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "lowerarm_r", None, -1))
        self.lineEdit_mh_joint_clavicle_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_clavicle_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "clavicle_l", None, -1))
        self.pushButton_add_mocap_lowerarm_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_lowerarm_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.label_3.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "Left Leg", None, -1))
        self.lineEdit_mh_joint_upperarm_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_upperarm_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "upperarm_l", None, -1))
        self.pushButton_add_mocap_ball_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_ball_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.lineEdit_mh_joint_pinky_03_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_pinky_03_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "pinky_03_r", None, -1))
        self.lineEdit_mh_joint_pinky_metacarpal_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_pinky_metacarpal_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "pinky_metacarpal_l", None, -1))
        self.lineEdit_mh_joint_index_01_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_index_01_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "index_01_r", None, -1))
        self.lineEdit_mh_joint_pinky_03_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_pinky_03_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "pinky_03_l", None, -1))
        self.lineEdit_mocap_joint_thumb_01_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_thumb_01_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_root.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_root.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mh_joint_thumb_02_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_thumb_02_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "thumb_02_l", None, -1))
        self.lineEdit_mh_joint_thumb_03_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_thumb_03_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "thumb_03_r", None, -1))
        self.lineEdit_mh_joint_thumb_01_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_thumb_01_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "thumb_01_r", None, -1))
        self.lineEdit_mh_joint_ring_01_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_ring_01_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "ring_01_r", None, -1))
        self.lineEdit_mh_joint_ring_02_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_ring_02_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "ring_02_r", None, -1))
        self.lineEdit_mh_joint_ring_03_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_ring_03_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "ring_03_l", None, -1))
        self.lineEdit_mh_joint_middle_03_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_middle_03_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "middle_03_l", None, -1))
        self.lineEdit_mh_joint_thumb_01_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_thumb_01_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "thumb_01_l", None, -1))
        self.lineEdit_mh_joint_middle_03_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_middle_03_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "middle_03_r", None, -1))
        self.lineEdit_mh_joint_index_01_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_index_01_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "index_01_l", None, -1))
        self.lineEdit_mh_joint_index_03_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_index_03_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "index_03_r", None, -1))
        self.lineEdit_mh_joint_pinky_metacarpal_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "source joint", None, -1))
        self.lineEdit_mh_joint_pinky_metacarpal_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "pinky_metacarpal_r", None, -1))
        self.lineEdit_mocap_joint_thumb_03_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_thumb_03_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_thumb_02_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_thumb_02_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_index_metacarpal_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_index_metacarpal_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_index_01_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_index_01_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_index_02_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_index_02_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_index_03_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_index_03_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_middle_metacarpal_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_middle_metacarpal_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_middle_01_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_middle_01_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_middle_02_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_middle_02_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_middle_03_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_middle_03_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_ring_metacarpal_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_ring_metacarpal_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_ring_01_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_ring_01_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_ring_02_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_ring_02_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_ring_03_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_ring_03_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_pinky_metacarpal_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_pinky_metacarpal_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_pinky_01_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_pinky_01_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_pinky_02_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_pinky_02_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_pinky_03_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_pinky_03_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_thumb_01_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_thumb_01_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_thumb_02_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_thumb_02_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_thumb_03_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_thumb_03_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_index_metacarpal_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_index_metacarpal_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_index_01_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_index_01_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_index_02_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_index_02_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_index_03_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_index_03_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_middle_metacarpal_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_middle_metacarpal_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_middle_01_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_middle_01_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_middle_02_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_middle_02_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_middle_03_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_middle_03_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_ring_metacarpal_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_ring_metacarpal_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_ring_01_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_ring_01_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_ring_02_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_ring_02_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_ring_03_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_ring_03_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_pinky_metacarpal_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_pinky_metacarpal_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_pinky_01_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_pinky_01_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_pinky_02_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_pinky_02_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.lineEdit_mocap_joint_pinky_03_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "target joint or control", None, -1))
        self.lineEdit_mocap_joint_pinky_03_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<motion source joint>", None, -1))
        self.pushButton_add_mocap_thumb_01_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_thumb_01_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_thumb_02_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_thumb_02_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_thumb_03_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_thumb_03_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_index_metacarpal_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_index_metacarpal_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_index_01_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_index_01_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_index_02_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_index_02_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_index_03_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_index_03_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_middle_metacarpal_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_middle_metacarpal_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_middle_01_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_middle_01_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_middle_02_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_middle_02_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_middle_03_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_middle_03_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_ring_metacarpal_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_ring_metacarpal_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_ring_01_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_ring_01_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_ring_02_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_ring_02_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_ring_03_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_ring_03_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_pinky_metacarpal_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_pinky_metacarpal_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_pinky_01_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_pinky_01_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_pinky_02_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_pinky_02_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_pinky_03_l.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_pinky_03_l.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_thumb_01_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_thumb_01_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_thumb_02_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_thumb_02_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_thumb_03_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_thumb_03_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_index_metacarpal_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_index_metacarpal_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_index_01_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_index_01_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_index_02_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_index_02_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_index_03_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_index_03_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_middle_metacarpal_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_middle_metacarpal_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_middle_01_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_middle_01_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_middle_02_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_middle_02_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_middle_03_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_middle_03_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_ring_metacarpal_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_ring_metacarpal_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_ring_01_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_ring_01_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_ring_02_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_ring_02_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_ring_03_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_ring_03_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_pinky_metacarpal_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_pinky_metacarpal_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_pinky_01_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_pinky_01_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_pinky_02_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_pinky_02_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))
        self.pushButton_add_mocap_pinky_03_r.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add selected object as target", None, -1))
        self.pushButton_add_mocap_pinky_03_r.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "add source", None, -1))


        #self.pushButton_copy_match_pose.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "Copy Match Pose", None, -1))
        #self.pushButton_copy_match_pose.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "Copy Match Pose", None, -1))

        self.pushButton_mirror_source_pose.setToolTip(QtWidgets.QApplication.translate("MGMetaMotionMatch", "Mirror Source Pose", None, -1))
        self.pushButton_mirror_source_pose.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "Mirror Source Pose", None, -1))

        self.pushButton_mirror_source_pose.setText(QCoreApplication.translate("MGMetaMotionMatch", "Mirror Source Pose", None))
        #self.pushButton_copy_match_pose.setText(QCoreApplication.translate("MGMetaMotionMatch", "Copy Match Pose", None))
        self.checkBox_mirror_invert.setText(QCoreApplication.translate("MGMetaMotionMatch", "Inverse", None))
        
        self.lineEdit_mirror_source.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<enter source direction>", None, -1))
        self.lineEdit_mirror_target.setText(QtWidgets.QApplication.translate("MGMetaMotionMatch", "<enter target direction>", None, -1))

class mg_meta_motion_match_GUI(Ui_MGMetaMotionMatch,QtWidgets.QMainWindow, QtWidgets.QDialog):
    def __init__(self):
        super(mg_meta_motion_match_GUI, self).__init__()     
        self.setupUi(self)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        
        self.pushButton_load_match_file.clicked.connect(self.load_match_file)
        self.pushButton_save_match_file.clicked.connect(self.save_match_file)
        self.pushButton_apply_mocap.clicked.connect(self.mgMocapApply)
        #self.pushButton_copy_match_pose.clicked.connect(partial(self.copy_match_pose,joint_list=[]))
        self.pushButton_mirror_source_pose.clicked.connect(self.mirror_source_pose)
        self.pushButton_add_mocap_root.clicked.connect(partial(self.updateMotionSource_runScript,'root'))
        self.pushButton_add_mocap_pelvis.clicked.connect(partial(self.updateMotionSource_runScript,'pelvis'))
        self.pushButton_add_mocap_spine_01.clicked.connect(partial(self.updateMotionSource_runScript,'spine_01'))
        self.pushButton_add_mocap_spine_02.clicked.connect(partial(self.updateMotionSource_runScript,'spine_02'))
        self.pushButton_add_mocap_spine_03.clicked.connect(partial(self.updateMotionSource_runScript,'spine_03'))
        self.pushButton_add_mocap_spine_04.clicked.connect(partial(self.updateMotionSource_runScript,'spine_04'))
        self.pushButton_add_mocap_spine_05.clicked.connect(partial(self.updateMotionSource_runScript,'spine_05'))
        self.pushButton_add_mocap_neck_01.clicked.connect(partial(self.updateMotionSource_runScript,'neck_01'))
        self.pushButton_add_mocap_neck_02.clicked.connect(partial(self.updateMotionSource_runScript,'neck_02'))
        self.pushButton_add_mocap_head.clicked.connect(partial(self.updateMotionSource_runScript,'head'))
        self.pushButton_add_mocap_clavicle_l.clicked.connect(partial(self.updateMotionSource_runScript,'clavicle_l'))
        self.pushButton_add_mocap_upperarm_l.clicked.connect(partial(self.updateMotionSource_runScript,'upperarm_l'))
        self.pushButton_add_mocap_lowerarm_l.clicked.connect(partial(self.updateMotionSource_runScript,'lowerarm_l'))
        self.pushButton_add_mocap_hand_l.clicked.connect(partial(self.updateMotionSource_runScript,'hand_l'))
        self.pushButton_add_mocap_clavicle_r.clicked.connect(partial(self.updateMotionSource_runScript,'clavicle_r'))
        self.pushButton_add_mocap_upperarm_r.clicked.connect(partial(self.updateMotionSource_runScript,'upperarm_r'))
        self.pushButton_add_mocap_lowerarm_r.clicked.connect(partial(self.updateMotionSource_runScript,'lowerarm_r'))
        self.pushButton_add_mocap_hand_r.clicked.connect(partial(self.updateMotionSource_runScript,'hand_r'))
        self.pushButton_add_mocap_thigh_l.clicked.connect(partial(self.updateMotionSource_runScript,'thigh_l'))
        self.pushButton_add_mocap_calf_l.clicked.connect(partial(self.updateMotionSource_runScript,'calf_l'))
        self.pushButton_add_mocap_foot_l.clicked.connect(partial(self.updateMotionSource_runScript,'foot_l'))
        self.pushButton_add_mocap_ball_l.clicked.connect(partial(self.updateMotionSource_runScript,'ball_l'))
        self.pushButton_add_mocap_thigh_r.clicked.connect(partial(self.updateMotionSource_runScript,'thigh_r'))
        self.pushButton_add_mocap_calf_r.clicked.connect(partial(self.updateMotionSource_runScript,'calf_r'))
        self.pushButton_add_mocap_foot_r.clicked.connect(partial(self.updateMotionSource_runScript,'foot_r'))
        self.pushButton_add_mocap_ball_r.clicked.connect(partial(self.updateMotionSource_runScript,'ball_r'))
        self.pushButton_add_mocap_thumb_01_l.clicked.connect(partial(self.updateMotionSource_runScript,'thumb_01_l'))
        self.pushButton_add_mocap_thumb_02_l.clicked.connect(partial(self.updateMotionSource_runScript,'thumb_02_l'))
        self.pushButton_add_mocap_thumb_03_l.clicked.connect(partial(self.updateMotionSource_runScript,'thumb_03_l'))
        self.pushButton_add_mocap_index_metacarpal_l.clicked.connect(partial(self.updateMotionSource_runScript,'index_metacarpal_l'))
        self.pushButton_add_mocap_index_01_l.clicked.connect(partial(self.updateMotionSource_runScript,'index_01_l'))
        self.pushButton_add_mocap_index_02_l.clicked.connect(partial(self.updateMotionSource_runScript,'index_02_l'))
        self.pushButton_add_mocap_index_03_l.clicked.connect(partial(self.updateMotionSource_runScript,'index_03_l'))
        self.pushButton_add_mocap_middle_metacarpal_l.clicked.connect(partial(self.updateMotionSource_runScript,'middle_metacarpal_l'))
        self.pushButton_add_mocap_middle_01_l.clicked.connect(partial(self.updateMotionSource_runScript,'middle_01_l'))
        self.pushButton_add_mocap_middle_02_l.clicked.connect(partial(self.updateMotionSource_runScript,'middle_02_l'))
        self.pushButton_add_mocap_ring_metacarpal_l.clicked.connect(partial(self.updateMotionSource_runScript,'ring_metacarpal_l'))
        self.pushButton_add_mocap_ring_01_l.clicked.connect(partial(self.updateMotionSource_runScript,'ring_01_l'))
        self.pushButton_add_mocap_ring_02_l.clicked.connect(partial(self.updateMotionSource_runScript,'ring_02_l'))
        self.pushButton_add_mocap_ring_03_l.clicked.connect(partial(self.updateMotionSource_runScript,'ring_03_l'))
        self.pushButton_add_mocap_middle_03_l.clicked.connect(partial(self.updateMotionSource_runScript,'middle_03_l'))
        self.pushButton_add_mocap_pinky_metacarpal_l.clicked.connect(partial(self.updateMotionSource_runScript,'pinky_metacarpal_l'))
        self.pushButton_add_mocap_pinky_01_l.clicked.connect(partial(self.updateMotionSource_runScript,'pinky_01_l'))
        self.pushButton_add_mocap_pinky_02_l.clicked.connect(partial(self.updateMotionSource_runScript,'pinky_02_l'))
        self.pushButton_add_mocap_pinky_03_l.clicked.connect(partial(self.updateMotionSource_runScript,'pinky_03_l'))
        self.pushButton_add_mocap_thumb_01_r.clicked.connect(partial(self.updateMotionSource_runScript,'thumb_01_r'))
        self.pushButton_add_mocap_thumb_02_r.clicked.connect(partial(self.updateMotionSource_runScript,'thumb_02_r'))
        self.pushButton_add_mocap_thumb_03_r.clicked.connect(partial(self.updateMotionSource_runScript,'thumb_03_r'))
        self.pushButton_add_mocap_index_metacarpal_r.clicked.connect(partial(self.updateMotionSource_runScript,'index_metacarpal_r'))
        self.pushButton_add_mocap_index_01_r.clicked.connect(partial(self.updateMotionSource_runScript,'index_01_r'))
        self.pushButton_add_mocap_index_02_r.clicked.connect(partial(self.updateMotionSource_runScript,'index_02_r'))
        self.pushButton_add_mocap_index_03_r.clicked.connect(partial(self.updateMotionSource_runScript,'index_03_r'))
        self.pushButton_add_mocap_middle_metacarpal_r.clicked.connect(partial(self.updateMotionSource_runScript,'middle_metacarpal_r'))
        self.pushButton_add_mocap_middle_01_r.clicked.connect(partial(self.updateMotionSource_runScript,'middle_01_r'))
        self.pushButton_add_mocap_middle_02_r.clicked.connect(partial(self.updateMotionSource_runScript,'middle_02_r'))
        self.pushButton_add_mocap_middle_03_r.clicked.connect(partial(self.updateMotionSource_runScript,'middle_03_r'))
        self.pushButton_add_mocap_ring_metacarpal_r.clicked.connect(partial(self.updateMotionSource_runScript,'ring_metacarpal_r'))
        self.pushButton_add_mocap_ring_01_r.clicked.connect(partial(self.updateMotionSource_runScript,'ring_01_r'))
        self.pushButton_add_mocap_ring_02_r.clicked.connect(partial(self.updateMotionSource_runScript,'ring_02_r'))
        self.pushButton_add_mocap_ring_03_r.clicked.connect(partial(self.updateMotionSource_runScript,'ring_03_r'))
        self.pushButton_add_mocap_pinky_metacarpal_r.clicked.connect(partial(self.updateMotionSource_runScript,'pinky_metacarpal_r'))
        self.pushButton_add_mocap_pinky_01_r.clicked.connect(partial(self.updateMotionSource_runScript,'pinky_01_r'))
        self.pushButton_add_mocap_pinky_02_r.clicked.connect(partial(self.updateMotionSource_runScript,'pinky_02_r'))
        self.pushButton_add_mocap_pinky_03_r.clicked.connect(partial(self.updateMotionSource_runScript,'pinky_03_r'))


    def define_lists(self):
        metahuman_skeleton = [
        'pelvis',
        'pelvis',
        'spine_01',
        'spine_02',
        'spine_03',
        'spine_04',
        'spine_05',
        'neck_01',
        'neck_02',
        'head',
        'clavicle_l',
        'upperarm_l',
        'lowerarm_l',
        'hand_l',
        'clavicle_r',
        'upperarm_r',
        'lowerarm_r',
        'hand_r',
        'thigh_l',
        'calf_l',
        'foot_l',
        'ball_l',
        'thigh_r',
        'calf_r',
        'foot_r',
        'ball_r',
        'thumb_01_l',
        'thumb_02_l',
        'thumb_03_l',
        'index_metacarpal_l',
        'index_01_l',
        'index_02_l',
        'index_03_l',
        'middle_metacarpal_l',
        'middle_01_l',
        'middle_02_l',
        'ring_metacarpal_l',
        'ring_01_l',
        'ring_02_l',
        'ring_03_l',
        'middle_03_l',
        'pinky_metacarpal_l',
        'pinky_01_l',
        'pinky_02_l',
        'pinky_03_l',
        'thumb_01_r',
        'thumb_02_r',
        'thumb_03_r',
        'index_metacarpal_r',
        'index_01_r',
        'index_02_r',
        'index_03_r',
        'middle_metacarpal_r',
        'middle_01_r',
        'middle_02_r',
        'middle_03_r',
        'ring_metacarpal_r',
        'ring_01_r',
        'ring_02_r',
        'ring_03_r',
        'pinky_metacarpal_r',
        'pinky_01_r',
        'pinky_02_r',
        'pinky_03_r',
        ]

        metahuman_ctrl = [
        'body_ctrl',
        'hips_ctrl',
        'spine_01_ctrl',
        'spine_02_ctrl',
        'spine_03_ctrl',
        'spine_04_ctrl',
        'spine_05_ctrl',
        'neck_01_ctrl',
        'neck_02_ctrl',
        'head_ctrl',
        'clavicle_l_ctrl',
        'upperarm_l_fk_ctrl',
        'lowerarm_l_fk_ctrl',
        'hand_l_fk_ctrl',
        'clavicle_r_ctrl',
        'upperarm_r_fk_ctrl',
        'lowerarm_r_fk_ctrl',
        'hand_r_fk_ctrl',
        'thigh_l_fk_ctrl',
        'calf_l_fk_ctrl',
        'foot_l_fk_ctrl',
        'ball_l_fk_ctrl',
        'thigh_r_fk_ctrl',
        'calf_r_fk_ctrl',
        'foot_r_fk_ctrl',
        'ball_r_fk_ctrl',
        'thumb_01_l_ctrl',
        'thumb_02_l_ctrl',
        'thumb_03_l_ctrl',
        'index_metacarpal_l_ctrl',
        'index_01_l_ctrl',
        'index_02_l_ctrl',
        'index_03_l_ctrl',
        'middle_metacarpal_l_ctrl',
        'middle_01_l_ctrl',
        'middle_02_l_ctrl',
        'middle_03_l_ctrl',
        'ring_metacarpal_l_ctrl',
        'ring_01_l_ctrl',
        'ring_02_l_ctrl',
        'ring_03_l_ctrl',
        'pinky_metacarpal_l_ctrl',
        'pinky_01_l_ctrl',
        'pinky_02_l_ctrl',
        'pinky_03_l_ctrl',
        'thumb_02_r_ctrl',
        'thumb_03_r_ctrl',
        'index_metacarpal_r_ctrl',
        'index_01_r_ctrl',
        'index_02_r_ctrl',
        'index_03_r_ctrl',
        'middle_metacarpal_r_ctrl',
        'middle_01_r_ctrl',
        'middle_02_r_ctrl',
        'middle_03_r_ctrl',
        'ring_metacarpal_r_ctrl',
        'ring_01_r_ctrl',
        'ring_02_r_ctrl',
        'ring_03_r_ctrl',
        'pinky_metacarpal_r_ctrl',
        'pinky_01_r_ctrl',
        'pinky_02_r_ctrl',
        'pinky_03_r_ctrl',
        ]

        return metahuman_skeleton, metahuman_ctrl
        
    def updateMotionSource_runScript(self, metahuman_joint_string):
        object_list = cmds.ls(sl=1)
        current_string = None
        if len(object_list) > 0:
            if ':' in object_list[0]:
                current_string = object_list[0].split(':')[-1]
            else:
                current_string = object_list[0]
        if current_string:
            exec('self.lineEdit_mocap_joint_'+metahuman_joint_string+'.setText(current_string)')

    def load_match_file(self):
        metahuman_skeleton, metahuman_ctrl = self.define_lists()
        usd = cmds.internalVar(usd=True)
        match_files_dir = usd + 'madguru_tools/match_files/'
        multipleFilters = "JSON Files Match and Pose (*.json);;Text Files Match Only (*.txt)"
        namespaceStrSrc, namespaceStrTrg = self.get_namespaces()

        auto_key_state = cmds.autoKeyframe(state=1, q=1)
        if not auto_key_state:
            cmds.autoKeyframe(state=True )

        start_frame=int(cmds.playbackOptions(q=1,minTime=1))
        cmds.currentTime(start_frame)

        if os.path.exists(str(match_files_dir)):
            fileLoadPath = str(cmds.fileDialog2(fileMode=1, dir=str(match_files_dir), caption="Load Match File", fileFilter=multipleFilters, fm=1)[0])
        else:
            fileLoadPath = str(cmds.fileDialog2(fileMode=1, caption="Load Match File", fileFilter=multipleFilters, fm=1)[0])
        match_list = []

        if fileLoadPath.endswith('.txt'):
            with open(fileLoadPath, 'r') as match_file:
                match_list = match_file.readlines()
            for val in match_list:
                if val == ' ' or val == '' or val == '  ' or len(val) == 1:
                    match_list.remove(val)

            for num in range(0, len(metahuman_skeleton)):
                if num <= len(match_list):
                    current_string = match_list[num]
                    exec('self.lineEdit_mocap_joint_' + metahuman_skeleton[num] + '.setText(current_string)')

        if fileLoadPath.endswith('.json'):
            # open json file
            json_file_path = fileLoadPath
            
            if json_file_path:
                json_string = ''
                with open(json_file_path) as json_file:
                    json_string = json.load(json_file)
                    json_data = json.loads(json_string)

            # read in dictionary
            match_list = None
            match_pose_list = None

            if 'joints' in json_data:
                match_list = json_data['joints']

            if 'pose' in json_data:
                match_pose_list = json_data['pose']
    
            # populate fields in UI
            if match_list:
                for num in range(0, len(metahuman_skeleton)):
                    if num <= len(match_list):
                        current_string = match_list[num].replace('/n','')
                        exec('self.lineEdit_mocap_joint_' + metahuman_skeleton[num] + '.setText(current_string)')

                # apply pose to character joints in scene
                if match_pose_list:
                    for object in match_list:
                        object = object.replace('\n', '')
                        if object in match_pose_list:
                            rotation_list = match_pose_list[object]
                            if cmds.objExists(namespaceStrSrc + object):
                                objectName = namespaceStrSrc + object
                                num=0
                                for letter in ['X', 'Y', 'Z']:
                                    #cmds.setAttr(objectName + '.rotate' + letter, lock=False)
                                    cmds.setAttr(objectName + '.rotate' + letter, rotation_list[num])
                                    cmds.setKeyframe(objectName, attribute='rotate' + letter)
                                    num+=1
                            else:
                                print('No object named ' + object + ' found. Please select a joint on your mocap/anim skeleton and load match file again.')
                        else:
                            if not '<motion source joint>' in object:
                                print('Skipping rotation loading for ' + object + ' as it was not found in the pose list.')


                    # parent con root into position
                    root_joint = namespaceStrSrc + match_list[0]
                    if not cmds.objExists(root_joint):
                        root_joint = namespaceStrSrc + match_list[1]

                    if cmds.objExists(root_joint):
                        for letter in ['X', 'Y', 'Z']:
                            cmds.setAttr(root_joint + '.translate' + letter, 0)
                            cmds.setAttr(root_joint + '.rotate' + letter, 0)
                    
                else:
                    print('Skippng pose matching. No match pose list found in file.')

            else:
                print('Skippng joint matching. No match list found in file.')
        if not auto_key_state:
            cmds.autoKeyframe( state=False )

    def save_match_file(self): 
        metahuman_skeleton, metahuman_ctrl = self.define_lists()
        usd = cmds.internalVar(usd=True)
        match_files_dir = usd + 'madguru_tools/match_files/'
        multipleFilters = "JSON Files Match and Pose (*.json);;Text Files Match Only (*.txt)"

        if os.path.exists(str(match_files_dir)):
            fileSavePath = str(cmds.fileDialog2(dir=str(match_files_dir), caption="Save Match File (Select Joint on Animated Skeleton to Save Pose)", fileFilter=multipleFilters, fm=0)[0])
        else:
            fileSavePath = str(cmds.fileDialog2(caption="Save Match File", fileFilter=multipleFilters, fm=0)[0])
        match_file = open(fileSavePath, "w")
        match_list = []

        for metahuman_joint_string in metahuman_skeleton:
            source_motion_joint = eval('self.lineEdit_mocap_joint_'+metahuman_joint_string+'.text()')
            match_list.append(source_motion_joint.replace('/n', ''))

        if fileSavePath.endswith('.txt'):
            for item in match_list:
                match_file.write("%s\n" % item)
            match_file.flush()
            match_file.close()

        if fileSavePath.endswith('.json'):
            namespace = ''
            match_rotation_list = []
            if len(cmds.ls(sl=1))>0:
                source_object = cmds.ls(sl=1)[0]
                if ':' in source_object:
                    strLs = source_object.split(':')
                for strNum in range(0, len(strLs)-1):
                    namespace += strLs[strNum]+':'
            if namespace:
                
                for object in match_list:
                    namespace=str(namespace)
                    object = str(object).replace('/n','')
                    match_rotation_list.append(namespace+object)
            else:
                match_rotation_list=match_list

            # create dictionary
            match_dict = {}
            match_dict['joints'] = match_list
            match_dict['pose'] = self.copy_match_pose(joint_list = match_rotation_list)

            # export json
            json_string = json.dumps(match_dict)
            json_data = json.loads(json_string)

            with open(fileSavePath, 'w') as match_file:
                json.dump(json_string, match_file)

        print('Saved match file ' +  fileSavePath)            

    def index_containing_substring(self, the_list, substring):
        for i, s in enumerate(the_list):
            if substring in s:
                  return i
        return -1
                    
    def mgMocapApply(self):
        print('Starting mgMocapApply...')
        object_list = cmds.ls(sl=1)
        source_object = None
        target_object = None
        delete_constraint_list = []

        if len(object_list)>1:    
            source_object, target_object, delete_constraint_list = self.mgMetahumanBodyMocapApply()
            if cmds.objExists(source_object):
                if cmds.objExists(target_object):
                    cmds.select(target_object)
                    self.mgMetahumanBodyMocapBake(delete_constraint_list=delete_constraint_list)
                else:
                    print(target_object + 'was not found.')
            else:
                print(source_object + 'was not found.')
        else:
            print('Please select a source and target object for motion transfer.')
        
    # select part of src and part of trg rigs
    def mgMetahumanBodyMocapApply(self):
        print('mgMetahumanBodyMocapApply begins...')
        cmds.refresh(suspend=True)
        source_object = None
        target_object = None
        delete_constraint_list = []

        object_list = cmds.ls(sl=1)
        if len(object_list)>1:
            source_object = object_list[0]
            target_object = object_list[1]

            start_frame = cmds.playbackOptions(q=1,minTime=1)
            end_frame = cmds.playbackOptions(q=1,maxTime=1)
            namespaceStrSrc = ''
            namespaceStrTrg = ''
            source_object = object_list[0]
            if ':' in source_object:
                strLs = source_object.split(':')
                for strNum in range(0, len(strLs)-1):
                    namespaceStrSrc += strLs[strNum]+':'
            else:
                if cmds.listRelatives(object_list[0], c=1):
                    child_list = cmds.listRelatives(object_list[0], c=1)
                    substring_in_list = any(':' in string for string in child_list)                    
                    if substring_in_list:
                        index = self.index_containing_substring(child_list, ':')
                        source_object = child_list[index]
                        
                        if ':' in source_object:
                            strLs = source_object.split(':')
                            for strNum in range(0, len(strLs)-1):
                                namespaceStrSrc += strLs[strNum]+':'

            if ':' in object_list[1]:
                strLs = object_list[1].split(':')
                for strNum in range(0, len(strLs)-1):
                    namespaceStrTrg += strLs[strNum]+':'
                                    
            metahuman_skeleton, metahuman_ctrl = self.define_lists()

            source_skeleton = []
            for metahuman_joint_string in metahuman_skeleton:
                source_motion_joint = eval('self.lineEdit_mocap_joint_'+metahuman_joint_string+'.text()')         
                source_skeleton.append(source_motion_joint)

            metahuman_joints = target_object_list(metahuman_skeleton = metahuman_skeleton, metahuman_ctrl = metahuman_ctrl, namespace = namespaceStrTrg)
            for num in range(0, len(metahuman_joints)):
                current_metahuman_joint = namespaceStrTrg + metahuman_joints[num].strip()
                if not cmds.objExists(current_metahuman_joint):
                    current_metahuman_joint = metahuman_joints[num].strip()

                current_mocap = namespaceStrSrc + source_skeleton[num].strip()

                if cmds.objExists(current_metahuman_joint):
                    if cmds.objExists(current_mocap):
                        translate_check, rotation_check, scale_check = check_axis(object = current_metahuman_joint, translate_check = 0, rotation_check = 1, scale_check = 0)
                        if not translate_check:
                            translate_check = 'none'
                        if not rotation_check:
                            rotation_check = 'none'
                        if not scale_check:
                            scale_check = 'none'
                        if translate_check == 'xyz':
                            translate_check = 'all'
                        if rotation_check == 'xyz':
                            rotation_check = 'all'
                        if scale_check == 'xyz':
                            scale_check = 'all'

                        if not num == 0 and not rotation_check == 'all' and not 'metacarpal' in current_metahuman_joint:
                            con_name = current_mocap + '_delete_con' + str(random())
                            try:
                                # rotation_check = finger_check(object = current_metahuman_joint, rotation_check = rotation_check)
                                cmds.orientConstraint(current_mocap, current_metahuman_joint, mo=1, sk=rotation_check, n=con_name)
                                delete_constraint_list.append(con_name)
                            except:
                                print('A: SkippingA ' + current_metahuman_joint + ' due to existing connection.')
                        else:
                            if num == 0 and not 'metacarpal' in current_metahuman_joint:
                                if not translate_check == 'all':
                                    con_name = current_mocap + '_delete_con' + str(random())
                                    cmds.pointConstraint(current_mocap, current_metahuman_joint, mo=1, sk=translate_check, n = con_name)
                                    delete_constraint_list.append(con_name)
                                if not rotation_check == 'all':
                                    con_name = current_mocap + '_delete_con' + str(random())
                                    cmds.orientConstraint(current_mocap, current_metahuman_joint, mo=1, sk=rotation_check, n = con_name)     
                            else:
                                if not translate_check == 'all' and not 'metacarpal' in current_metahuman_joint:
                                    try:
                                        cmds.pointConstraint(current_mocap, current_metahuman_joint, mo=1, sk=translate_check, n = con_name)
                                        delete_constraint_list.append(con_name)
                                    except:
                                        print('D: Skipping ' + current_metahuman_joint + ' due to existing connection.')
                                if not rotation_check == 'all' and not 'metacarpal' in current_metahuman_joint:
                                    try:
                                        # rotation_check = finger_check(object = current_metahuman_joint, rotation_check = rotation_check)
                                        cmds.orientConstraint(current_mocap, current_metahuman_joint, mo=1, sk=rotation_check, n = con_name)
                                        delete_constraint_list.append(con_name)
                                    except:
                                        print('E: Skipping ' + current_metahuman_joint + ' due to existing connection.')
                            
        # key IK to match FK
        dir_str_list = ['l', 'r']
        part_str_list = ['hand', 'foot']
        start_frame=int(cmds.playbackOptions(q=1,minTime=1))
        end_frame=int(cmds.playbackOptions(q=1,maxTime=1))
        
        auto_key_state = cmds.autoKeyframe(state=1, q=1)
        if not auto_key_state:
            cmds.autoKeyframe(state=True )
        ikfk_object_list = []
        for current_dir in dir_str_list:
            for current_part in part_str_list:
                current_object = namespaceStrTrg + current_part + '_' + current_dir + '_ik_ctrl'
                if cmds.objExists(current_object):
                    ikfk_object_list.append(current_object)
        ik_fk_match(start_frame = start_frame, end_frame = end_frame, object_list=ikfk_object_list)

        if not auto_key_state:
            cmds.autoKeyframe( state=False )

        return source_object, target_object, delete_constraint_list
        
    def mgMetahumanBodyMocapBake(self, delete_constraint_list=[]):
        print('Starting mgMetahumanBodyMocapBake...')
        metahuman_skeleton, metahuman_ctrl = self.define_lists()
        start_frame=int(cmds.playbackOptions(q=1,minTime=1))
        end_frame=int(cmds.playbackOptions(q=1,maxTime=1))
        object_list = cmds.ls(sl=1)
        namespace = ''
        
        if ':' in object_list[0]:
            strLs = object_list[0].split(':')
            for strNum in range(0, len(strLs)-1):
                namespace += strLs[strNum]+':'
        ns_bodyCtrlLs = target_object_list(metahuman_skeleton = metahuman_skeleton, metahuman_ctrl = metahuman_ctrl, namespace = namespace)
        cmds.select(cl=1)

        for obj in ns_bodyCtrlLs:
            if cmds.objExists(obj):
                cmds.select(obj, add=1)        
            else:
                print('not found ' + obj)
        cmds.bakeResults(t=(start_frame, end_frame), at = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz'], bakeOnOverrideLayer=True, simulation=True)
        cmds.select(cl=1)
        if len(delete_constraint_list)>0:
            for constraint_string in delete_constraint_list:
                if cmds.objExists(str(constraint_string)):
                    cmds.select(str(constraint_string), add=1)
                    cmds.delete()

        # Find the animation curves of the locator
        cmds.select(ns_bodyCtrlLs[0])
        cmds.select(hi=1)
        animCurves = cmds.listConnections(cmds.ls(sl=1), d=1, type='animCurve')

        # filter_key_values(object_list=ns_bodyCtrlLs)

        #running euler filter on curves
        cmds.filterCurve(animCurves)
        
        cmds.refresh(suspend=False)

    def copy_match_pose(self, joint_list=None):
        # get selected joints
        if not joint_list:
            joint_list = cmds.ls(selection=True, type='joint')

        # create empty dictionary
        rotation_dict = {}
        # loop through joints and get their rotation values
        for joint in joint_list:
            joint=str(joint.replace('\n',''))
            if cmds.objExists(joint):
                x_rotation = cmds.getAttr(joint+'.rotateX')
                y_rotation = cmds.getAttr(joint+'.rotateY')
                z_rotation = cmds.getAttr(joint+'.rotateZ')

                # add rotation values to dictionary with joint name as key
                key = joint
                if ':' in joint:
                    key = str(joint.split(':')[-1])
                rotation_dict[key] = [x_rotation, y_rotation, z_rotation]
            else:
                if not '<motion source joint>' in joint:
                    print('Skipping ' + joint + ' does not exist.')
        return(rotation_dict)

    def mirror_source_pose(self):
        print('Running mirror_source_pose')
        source_str = self.lineEdit_mirror_source.text()
        target_str = self.lineEdit_mirror_target.text()
        invert = 1
        if self.checkBox_mirror_invert.isChecked():
            invert = -1
        joint_list = cmds.ls(sl=1)

        if source_str and target_str and joint_list:
            for source_joint in joint_list:
                target_joint = source_joint.replace(source_str, target_str)
                if cmds.objExists(target_joint):
                    x_rotation = cmds.getAttr(source_joint+'.rotateX')
                    y_rotation = cmds.getAttr(source_joint+'.rotateY')
                    z_rotation = cmds.getAttr(source_joint+'.rotateZ')

                    if invert:
                        x_rotation = x_rotation * -1
                        y_rotation = y_rotation * -1
                        z_rotation = z_rotation * -1
            
                    cmds.setAttr(target_joint+'.rotateX', x_rotation * invert)
                    cmds.setAttr(target_joint+'.rotateY', y_rotation * invert)
                    cmds.setAttr(target_joint+'.rotateZ', z_rotation * invert)            

                else:
                    print(target_joint + ' not found, skipping.')

    def get_namespaces(self):
        namespaceStrSrc=''
        namespaceStrTrg=''
        object_list = cmds.ls(sl=1)
        if len(object_list)>1:
            source_object = object_list[0]
            target_object = object_list[1]

            start_frame = cmds.playbackOptions(q=1,minTime=1)
            end_frame = cmds.playbackOptions(q=1,maxTime=1)
            namespaceStrSrc = ''
            namespaceStrTrg = ''
            source_object = object_list[0]
            if ':' in source_object:
                strLs = source_object.split(':')
                for strNum in range(0, len(strLs)-1):
                    namespaceStrSrc += strLs[strNum]+':'
            else:
                if cmds.listRelatives(object_list[0], c=1):
                    child_list = cmds.listRelatives(object_list[0], c=1)
                    substring_in_list = any(':' in string for string in child_list)                    
                    if substring_in_list:
                        index = self.index_containing_substring(child_list, ':')
                        source_object = child_list[index]
                        
                        if ':' in source_object:
                            strLs = source_object.split(':')
                            for strNum in range(0, len(strLs)-1):
                                namespaceStrSrc += strLs[strNum]+':'

            if ':' in object_list[1]:
                strLs = object_list[1].split(':')
                for strNum in range(0, len(strLs)-1):
                    namespaceStrTrg += strLs[strNum]+':'
        else:
            print('Please select the an object from the source skeleton and one from the metahuman skeleton to get namespaces.')

        return namespaceStrSrc, namespaceStrTrg

def unlock_axis(object = ''):
    axis = ['X', 'Y', 'Z']
    attrs = ['translate', 'rotate', 'scale']

    for ax in axis:
        for attr in attrs:
            cmds.setAttr(object+'.' + attr + ax, lock=0)

def check_axis(object = '', translate_check = 1, rotation_check = 1, scale_check = 1):
    axis = ['X', 'Y', 'Z']
    finger_list = ['pinky', 'ring', 'middle', 'index', 'thumb']
    use_axis_translate = ''
    use_axis_rotation = ''
    use_axis_scale = ''

    for ax in axis:
            if translate_check:
                check_value = cmds.getAttr(object+'.' + 'translate' + ax, se=1)
                if not check_value:
                    use_axis_translate = use_axis_translate + ax.lower()
            if rotation_check:
                check_value = cmds.getAttr(object+'.' + 'rotate' + ax, se=1)
                if not check_value:
                    use_axis_rotation = use_axis_rotation + ax.lower()
            if scale_check:
                check_value = cmds.getAttr(object+'.' + 'scale' + ax, se=1)
                if not check_value:
                    use_axis_scale = use_axis_scale + ax.lower()

    return use_axis_translate, use_axis_rotation, use_axis_scale

def finger_lock(object='', lock=1):
    cmds.setAttr(object + '.rotateX', lock = lock)
    finger_list = ['_pinky_', '_ring_', '_middle_', '_index_', '_thumb_']

def filter_key_values(object_list=[]):
    layer_exists = cmds.animLayer("BakeResults", query=True, ex=1)
    #if layer_exists:
        #mel.eval('selectLayer("BakeResults")')
    start_frame=int(cmds.playbackOptions(q=1,minTime=1))
    end_frame=int(cmds.playbackOptions(q=1,maxTime=1))
    auto_key_state = cmds.autoKeyframe(state=1, q=1)
    if not auto_key_state:
        cmds.autoKeyframe(state=True)    
    dir_list = ['X','Y','Z']
    finger_list = ['pinky_', 'ring_', 'middle_', 'index_', 'thumb_']

    for object in object_list:
        for finger_str in finger_list:
            if finger_str in object:
                for dir in dir_list:
                    try:
                        cmds.setAttr(object + '.translate' + dir, 0)
                        cmds.setKeyframe(object, at='translate' + dir, v=0)
                        if layer_exists:
                            cmds.setKeyframe(object, at='translate' + dir, v=0, al='BakeResults')
                    except:
                        dir = dir
                    rot_val = cmds.getAttr(object + '.rotate' + dir)
                    '''
                    if rot_val>=360:
                        rot_val = rot_val % 360
                        cmds.setAttr(object + '.rotate' + dir, rot_val)
                        if layer_exists:
                            cmds.setKeyframe(object, at='rotate' + dir, v=rot_val, al='BakeResults')
                        #else:
                        cmds.setKeyframe(object, at='rotate' + dir, v=rot_val)
                        '''
                        
                    if finger_str + '02' in object or finger_str + '03' in object or 'metacarpal' in object and not dir == 'Z':
                        cmds.setAttr(object + '.rotate' + dir, 0)
                        cmds.setKeyframe(object, at='rotate' + dir, v=0)
                        if layer_exists:
                            cmds.setKeyframe(object, at='rotate' + dir, v=0,  al='BakeResults')
                        
    if not auto_key_state:
        cmds.autoKeyframe( state=False )

def finger_check(object = '', rotation_check=''):
    finger_list = ['pinky_', 'ring_', 'middle_', 'index_', 'thumb_']
    for finger_str in finger_list:
        if finger_str in object:
            if rotation_check == None:
                rotation_check = 'x'
            if not 'x' in rotation_check:
                rotation_check = rotation_check + 'x'
            if finger_str + '02' in object or finger_str + '03' in object or 'metacarpal' in object:
                if rotation_check == None:
                    rotation_check = 'y'
                if not 'y' in rotation_check:
                    rotation_check = rotation_check + 'y'
        return rotation_check

def ik_fk_match(start_frame = None, end_frame = None, object_list=[]):
    if not start_frame:
        start_frame = int(cmds.currentTime(q=1))
    if not end_frame:
        end_frame = int(cmds.currentTime(q=1))

    if len(object_list)==0:
        if len(cmds.ls(sl=1))>0:
            object_list = cmds.ls(sl=1)
    
    if len(object_list)>0:
        for current_frame in range(int(start_frame), int(end_frame)+1):
            for object in object_list:
                namespace=''
                type_str=''
                limb = ''    
                match_transform = 0
    
                if 'arm' in object or 'hand' in object:
                    limb = 'arm'
    
                if 'leg' in object or 'foot' in object or 'thigh' in object or 'calf' in object:
                    limb = 'leg'

                if ':' in object:
                    namespace = object.split(':')[0]+':'
                if '_r_' in object:
                    dir_str = 'r'
                if '_l_' in object:
                    dir_str = 'l'
                if '_ik_' in object:
                    type_str = 'ik'
                if '_fk_' in object:
                    type_str = 'fk'
    
                if limb and type_str and dir_str:
                    fk_arm_target_list = ['upperarm_' + dir_str + '_fk_ctrl',
                    'lowerarm_' + dir_str + '_fk_ctrl',
                    'hand_' + dir_str + '_fk_ctrl',
                    'arm_pole_vector_' + dir_str + '_match']
        
                    ik_arm_source_list =['upperarm_' + dir_str + '_ik_motion',
                    'lowerarm_' + dir_str + '_ik_motion',
                    'hand_' + dir_str + '_ik_ctrl',
                    'arm_pole_vector_' + dir_str + '_ctrl']
        
                    fk_leg_target_list =['thigh_' + dir_str + '_fk_ctrl',
                    'calf_' + dir_str + '_fk_ctrl',
                    'foot_' + dir_str + '_fk_ctrl',
                    'ball_' + dir_str + '_fk_ctrl',
                    'leg_pole_vector_' + dir_str + '_match']
        
                    ik_leg_source_list = ['thigh_' + dir_str + '_ik_motion',
                    'calf_' + dir_str + '_ik_motion',
                    'foot_' + dir_str + '_ik_ctrl',
                    'ball_lift_' + dir_str + '_ik_ctrl',
                    'leg_pole_vector_' + dir_str + '_ctrl']
    
                    fk_arm_source_list = ['hand_' + dir_str + '_fk_ctrl',
                    'arm_pole_vector_' + dir_str + '_match']
    
                    ik_arm_target_list =['hand_' + dir_str + '_ik_ctrl',
                    'arm_pole_vector_' + dir_str + '_ctrl']
    
                    fk_leg_source_list =['foot_' + dir_str + '_fk_ctrl', 'ball_' + dir_str + '_fk_ctrl',
                    'leg_pole_vector_' + dir_str + '_match']
            
                    ik_leg_target_list = ['foot_' + dir_str + '_ik_ctrl', 'ball_lift_' + dir_str + '_ik_ctrl',
                    'leg_pole_vector_' + dir_str + '_ctrl']
    
                    if limb == 'arm':
                        if type_str == 'ik':
                            source_list = fk_arm_source_list
                            target_list = ik_arm_target_list
                            match_transform = 1
                
                        if type_str == 'fk':
                            source_list = ik_arm_source_list
                            target_list = fk_arm_target_list
                
                    if limb == 'leg':
                        if type_str == 'ik':
                            source_list = fk_leg_source_list
                            target_list = ik_leg_target_list
                            match_transform = 1
                
                        if type_str == 'fk':
                            source_list = ik_leg_source_list
                            target_list = fk_leg_target_list

                    if not int(cmds.currentTime(q=1)) == current_frame:
                        cmds.currentTime(current_frame)
                    for num in range(0, len(source_list)):
                        if cmds.objExists(namespace+target_list[num]) and cmds.objExists(namespace+source_list[num]):
                            cmds.matchTransform(namespace+target_list[num], namespace+source_list[num], pos = match_transform, rot=1)
                            if current_frame == start_frame:
                                keyframe_axis(object = namespace+target_list[num])

    else:
        print('Please select a hand or leg ik or fk control to apply match to.')

def keyframe_axis(object = ''):
    axis = ['X', 'Y', 'Z']
    attrs = ['translate', 'rotate']

    for ax in axis:
        for attr in attrs:
            if cmds.getAttr(object+'.' + attr + ax, se=1):
                cmds.setKeyframe(object+'.' + attr + ax, time=(cmds.currentTime(q=1), cmds.currentTime(q=1)))

def target_object_list(metahuman_skeleton = [], metahuman_ctrl = [], namespace = ''):
    ns_bodyCtrlLs = []
    if cmds.objExists(namespace + 'body_ctrl'):
        for obj in metahuman_ctrl:
            ns_bodyCtrlLs.append(namespace + obj)
    else:
        for obj in metahuman_skeleton:
            ns_bodyCtrlLs.append(str(namespace) + str(obj) + '_drv')

    return ns_bodyCtrlLs


        
# try:
#     mgmmm
# except NameError:
#     var_exists = False
# else:
#     var_exists = True
# if var_exists:
#     if mgmmm:
#         mgmmm.close()    
# mgmmm = mg_meta_motion_match_GUI()
# mgmmm.close()
# mgmmm.show()

