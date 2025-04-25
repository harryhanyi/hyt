from mhy.qt.core import QtWidgets


class SkinTransferConfig(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.currentNodeType = None
        main_layout = QtWidgets.QVBoxLayout()
        content_layout = QtWidgets.QVBoxLayout(self)
        self.setLayout(main_layout)
        self.setSizePolicy(QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Maximum)
        transfer_method_layout = QtWidgets.QHBoxLayout()
        transfer_method_label = QtWidgets.QLabel("Surface Associations:")
        self.transfer_method_combo = QtWidgets.QComboBox(self)
        transfer_method_layout.addWidget(transfer_method_label)
        self.transfer_method_combo.addItems(['closestPoint', 'rayCast',
                                             'closestComponent', 'UvSpace',
                                             "vertexId"])
        transfer_method_layout.addWidget(self.transfer_method_combo)

        line = QtWidgets.QFrame(self)
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)

        label = QtWidgets.QLabel("** The following options are skin cluster only **")
        self.ia_widget = QtWidgets.QWidget(self)
        ia_layout = QtWidgets.QGridLayout()
        ia_layout.setContentsMargins(0, 0, 0, 0)
        self.ia_widget.setLayout(ia_layout)
        ia_methods = ['None', "closestJoint", "oneToOne", "label", "name"]
        inf_association_one_label = QtWidgets.QLabel("Influence Association 1:")
        self.inf_association_one_combo = QtWidgets.QComboBox()
        self.inf_association_one_combo.addItems(ia_methods)
        self.inf_association_one_combo.setCurrentText('Closest joint')
        inf_association_two_label = QtWidgets.QLabel("Influence Association 2:")
        self.inf_association_two_combo = QtWidgets.QComboBox()
        self.inf_association_two_combo.addItems(ia_methods)
        inf_association_three_label = QtWidgets.QLabel("Influence Association 3:")
        self.inf_association_three_combo = QtWidgets.QComboBox()
        self.inf_association_three_combo.addItems(ia_methods)
        ia_layout.addWidget(inf_association_one_label, 0, 0)
        ia_layout.addWidget(self.inf_association_one_combo, 0, 1)
        ia_layout.addWidget(inf_association_two_label, 1, 0)
        ia_layout.addWidget(self.inf_association_two_combo, 1, 1)
        ia_layout.addWidget(inf_association_three_label, 2, 0)
        ia_layout.addWidget(self.inf_association_three_combo, 2, 1)

        self.normalize_check = QtWidgets.QCheckBox('Normalize', self)
        content_layout.addLayout(transfer_method_layout)
        content_layout.addWidget(line)
        content_layout.addWidget(label)
        content_layout.addWidget(self.ia_widget)
        content_layout.addWidget(self.normalize_check)

    def get_config(self):
        config = dict()
        config['surfaceAssociation'] = self.transfer_method_combo.currentText()
        config['normalize'] = self.normalize_check.isChecked()
        ias = [
            self.inf_association_one_combo.currentText(),
            self.inf_association_two_combo.currentText(),
            self.inf_association_three_combo.currentText()
        ]

        ias = [i for i in ias if i != "None"]
        if ias:
            config['influenceAssociation'] = ias
        else:
            config['influenceAssociation'] = None
        return config

    def read_config(self, config):
        if not config:
            return
        transfer_method = config.get('surfaceAssociation', 'closestPoint')
        self.transfer_method_combo.setCurrentText(transfer_method)
        normalized = config.get('normalize', True)
        self.normalize_check.setChecked(normalized)
        influence_association = config.get('influenceAssociation', None)
        for idx, combo in enumerate([self.inf_association_one_combo,
                                     self.inf_association_two_combo,
                                     self.inf_association_three_combo]):
            if influence_association and len(influence_association) > idx:
                combo.setCurrentText(influence_association[idx])
            else:
                combo.setCurrentText('None')
