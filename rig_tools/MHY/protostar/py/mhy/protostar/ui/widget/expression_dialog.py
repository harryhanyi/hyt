"""

This dialog will prompt when user promote parameters of an action to its graph

"""

import re
from mhy.qt.core.Qt import QtWidgets, QtGui, QtCore
import mhy.protostar.ui.manager as manager


class ExpressionDialog(QtWidgets.QDialog):
    def __init__(self, parameter, parent=None):
        super(ExpressionDialog, self).__init__(parent=parent)
        self.setWindowTitle(
            "Edit Expression on {}?".format(parameter.name)
        )

        self.parameter = parameter

        owner = parameter.owner

        self.script_editor = ExpressionEditor(owner, self)

        if self.parameter.script:
            self.script_editor.setText(parameter.script.code)

        layout = QtWidgets.QVBoxLayout()

        self.setMinimumWidth(450)
        self.setLayout(layout)

        layout.addWidget(self.script_editor)
        accept_pb = QtWidgets.QPushButton("Apply", self)
        layout.addWidget(accept_pb)
        accept_pb.clicked.connect(self.apply_cb)

    def apply_cb(self):
        """
        Called when apply button clicked. Check validation of arguments before
        promote the parameter to graph

        """
        expression = self.script_editor.toPlainText()
        try:
            self.parameter.script = expression
        except BaseException as e:
            self.warning_line.show()
            self.warning_line.setText(str(e))
            return

        owner = self.parameter.owner
        graph = owner.graph
        # Once a parameter has been prompt
        # 1. Refresh node scene for parent graph
        # 2. Refresh the state of promoted parameter

        manager.SignalManager.graph_updated_signal.emit(graph)

        # Reload the graph parameter panel
        manager.SignalManager.reload_graph_parameters_signal.emit(
            graph
        )
        manager.SignalManager.parameter_connection_changed_signal.emit(
            self.parameter
        )
        manager.SignalManager.repaint_lines_signal.emit()

        self.close()


class ExpressionEditor(QtWidgets.QTextEdit):
    parameter_search_pattern = "[{]([A-Za-z0-9_]+)[.]([A-Za-z0-9]*)$"

    def __init__(self, instance, parent=None):
        super(ExpressionEditor, self).__init__(parent=parent)

        self.objects = dict()
        self.completer = ExpCompleter(parent=self)
        self.completer.setWidget(self)
        self.completer.insertText.connect(self.insertCompletion)
        self.update_instance(instance)

    def insertCompletion(self, completion):
        tc = self.textCursor()
        extra = (len(completion) - len(self.completer.completionPrefix()))
        tc.movePosition(QtGui.QTextCursor.Left)
        tc.movePosition(QtGui.QTextCursor.EndOfWord)
        tc.insertText(completion[-extra:])
        self.setTextCursor(tc)
        self.completer.popup().hide()

    def focusInEvent(self, event):
        if self.completer:
            self.completer.setWidget(self)
        super(ExpressionEditor, self).focusInEvent(event)

    def keyPressEvent(self, event):
        super(ExpressionEditor, self).keyPressEvent(event)
        tc = self.textCursor()
        if (event.key() == QtCore.Qt.Key_Tab or
            event.key() == QtCore.Qt.Key_Return or
            event.key() == QtCore.Qt.Key_Enter) \
                and self.completer.popup().isVisible():
            self.completer.insertText.emit(self.completer.getSelected())
            self.completer.setCompletionMode(
                QtWidgets.QCompleter.PopupCompletion)
            return

        tc.select(QtGui.QTextCursor.WordUnderCursor)
        word = tc.selectedText()
        if word == '.':
            word = ''

        tc.select(QtGui.QTextCursor.LineUnderCursor)
        line = tc.selectedText()

        cr = self.cursorRect()
        if line.endswith('.' + word):
            results = re.findall(self.parameter_search_pattern, line)
            if results:
                pair = results[-1]
                action, param = pair
                self.set_completer_to_parameters(action, exclude=word)
                self.completer.setCompletionPrefix(param)
                popup = self.completer.popup()
                popup.setCurrentIndex(
                    self.completer.completionModel().index(0, 0))
                cr.setWidth(popup.sizeHintForColumn(0) +
                            popup.verticalScrollBar().sizeHint().width())
                self.completer.complete(cr)
                return
        elif line.endswith('{' + word):
            self.set_completer_to_actions(exclude=word)
            self.completer.setCompletionPrefix(word)
            popup = self.completer.popup()
            popup.setCurrentIndex(self.completer.completionModel().index(0, 0))
            cr.setWidth(popup.sizeHintForColumn(0) +
                        popup.verticalScrollBar().sizeHint().width())
            self.completer.complete(cr)
            return

        else:
            self.completer.popup().hide()

    def update_instance(self, instance):
        self.objects = {}
        graph = instance.graph
        if graph:
            for i in graph.iter_objects(skip_self=False):
                self.objects[i.name] = i
        else:
            self.objects[instance.name] = instance

    def set_completer_to_actions(self, exclude=''):
        model = self.completer.model()
        action_names = [i for i in self.objects.keys() if i!=exclude]
        model.setStringList(action_names)

    def set_completer_to_parameters(self, action, exclude=''):
        model = self.completer.model()
        param_names = []
        instance = self.objects.get(action)
        if instance:
            parameters = instance.get_params()
            param_names = [i.name for i in parameters if not i.name == exclude]
        model.setStringList(param_names)


class ExpCompleter(QtWidgets.QCompleter):
    insertText = QtCore.Signal(str)

    def __init__(self, parent=None):
        super(ExpCompleter, self).__init__([], parent=parent)
        self.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
        self.highlighted.connect(self.setHighlighted)

    def setHighlighted(self, text):
        self.lastSelected = text

    def getSelected(self):
        return self.lastSelected
