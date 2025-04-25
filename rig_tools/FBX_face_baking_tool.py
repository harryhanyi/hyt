from PySide2 import QtWidgets, QtCore
from maya import cmds


class FaceBakingUI(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(FaceBakingUI, self).__init__(parent)
        self.setWindowTitle("Baking Facial Tool")
        self.setMinimumWidth(300)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.build_ui()
        self.root = self.root_text_field.text()
        self.face_root = self.face_text_field.text()
        self.name_space = 'stella_shapeFace_rig'

    def build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)

        # Row 1: Text field + button
        row1 = QtWidgets.QHBoxLayout()
        self.root_text_field = QtWidgets.QLineEdit("Root_M")
        self.root_text_field.textChanged.connect(self.update_text_field)
        btn1 = QtWidgets.QPushButton("update Root_M")
        btn1.clicked.connect(lambda: self.update_root())
        row1.addWidget(self.root_text_field)
        row1.addWidget(btn1)

        # Row 2: Text field + button
        row2 = QtWidgets.QHBoxLayout()
        self.face_text_field = QtWidgets.QLineEdit("stella_shapeFace_rig:RIG")
        self.face_text_field.textChanged.connect(self.update_text_field)
        btn2 = QtWidgets.QPushButton("update Face Root")
        btn2.clicked.connect(lambda: self.update_face_root())
        row2.addWidget(self.face_text_field)
        row2.addWidget(btn2)

        # Bottom buttons
        button_row = QtWidgets.QHBoxLayout()
        bake_to_face_btn = QtWidgets.QPushButton("Bake Root to Face UI")
        bake_to_root_btn = QtWidgets.QPushButton("Bake Face UI to Root")
        bake_to_face_btn.clicked.connect(self.root_bake_to_ui)
        bake_to_root_btn.clicked.connect(self.ui_bake_to_root)
        button_row.addWidget(bake_to_face_btn)
        button_row.addWidget(bake_to_root_btn)

        # Add everything to the layout
        layout.addLayout(row1)
        layout.addLayout(row2)
        layout.addLayout(button_row)

    def update_root(self):
        sel = cmds.ls(selection=True)[0]
        if 'Root_M' in sel:
            self.root = sel
            self.root_text_field.setText(self.root)
        else:
            raise ValueError('Seletion is not animation skeleton root!')
    
    def update_face_root(self):
        sel = cmds.ls(selection=True)[0]
        if ':' in sel:
            self.name_space = sel.split(':')[0]
        else:
            raise ValueError('Selection is not referenced face rig!')
        
        temp_face_root = f'{self.name_space}:RIG'
        if f'{self.name_space}:GRP_faceGUI' in cmds.listRelatives(temp_face_root, ad=True):
            self.face_root = temp_face_root
            self.face_text_field.setText(self.face_root)
        else:
            raise ValueError('Selection is not referenced face rig!')
        return
    
    def update_text_field(self, new_text):
        sender = self.sender()
        if sender == self.root_text_field:
            self.root = new_text
        elif sender == self.face_text_field:
            self.face_root = new_text
        return

    def tokenize_attr(self, attr_name):
        channel = attr_name.split('_')[-1]
        ctrl_name = attr_name.replace(f'_{channel}', '')
        return ctrl_name, channel

    def root_bake_to_ui(self, to_root=False):
        start = cmds.playbackOptions(q=True, min=True)
        end = cmds.playbackOptions(q=True, max=True)
        attrs = cmds.listAttr(self.root, userDefined=True)
        attr_list = []
        for attr in attrs:
            ctrl, channel = self.tokenize_attr(attr)
            face_ctrl = f'{self.name_space}:{ctrl}'
            if cmds.objExists(face_ctrl):
                attr_list.append([f'{self.root}.{attr}',f'{face_ctrl}.{channel}'])

        cmds.refresh(suspend=True)

        for frame in range(int(start), int(end)+1):
            cmds.currentTime(frame, edit=True)
            for attrs in attr_list:
                root_attr = attrs[0]
                ctrl_attr = attrs[1]
                if not to_root:
                    value = cmds.getAttr(root_attr)
                    temp_attr = ctrl_attr
                else:
                    value = cmds.getAttr(ctrl_attr)
                    temp_attr = root_attr
                cmds.setKeyframe(temp_attr, value=value)

        cmds.refresh(suspend=False)
        return
    
    def ui_bake_to_root(self):
        self.root_bake_to_ui(to_root=True)
        
