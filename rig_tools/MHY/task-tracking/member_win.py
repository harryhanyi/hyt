import os
import json
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QTableWidget, QTableWidgetItem
from PyQt6.QtWidgets import QMenu, QComboBox, QLineEdit, QStyledItemDelegate
from PyQt6.QtGui import QAction
from PyQt6 import uic

from jira_util import JiraUtil


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class MemberWin(QMainWindow):
    def __init__(self):
        super().__init__()

        # Read Config JSON
        try:
            with open(BASE_DIR+"/account_config.json", "r") as file:
                self.account_config = json.load(file)
        except FileNotFoundError:
            print(f"File not found: account_config.json")
        except json.JSONDecodeError:
            print(f"Invalid JSON format in file: account_config.json")
        except Exception as e:
            print(f"Error occurred while reading account_config.json: {str(e)}")
        

        ###############################################################################
        # Set up Jira
        with open(BASE_DIR+"/jira_config.json", "r") as file:
            jira_config = json.load(file)
        self.jira = JiraUtil(
            jira_config["base_url"], 
            jira_config["admin_email"], 
            jira_config["admin_token"], 
            jira_config["project_key"],
            jira_config["pm"]
        )

        ###############################################################################
        # Load ui file
        uic.loadUi(BASE_DIR+"/member_win.ui", self)

        # Connect signals and slots
        self.button_submit.clicked.connect(self.log_time)
        self.tableWidget.cellClicked.connect(self.update_line_edit)

        # Fill ui data
        self.update_data_table()

        # Set up tableWidget custom delegate for task editing
        delegate = CustomDelegate(self.tableWidget, self.jira)
        self.tableWidget.setItemDelegate(delegate)

    def log_time(self):
        task_key = self.lineEdit_id.text()
        # Check task key input
        if len(task_key) <= 0:
            self.popout_dialog("Error", "Please select one task in the table to continue.")
            return

        # Check time input
        day_text = self.lineEdit_time_day.text()
        hour_text = self.lineEdit_time_hour.text()
        if len(day_text) <= 0 or len(hour_text) <= 0:
            self.popout_dialog("Error", "Time cannot be empty.")
            return
        try:
            day_int = int(day_text)
            hour_int = int(hour_text)
        except ValueError:
            self.popout_dialog("Error", "Time needs to be integer.")
            return

        # Send data to Jira
        time = int(day_text) * 8 + int(hour_text)
        check = self.jira.edit_task(task_key, "log", time)
        if check:
            self.popout_dialog("Success", "Task edited successfully!")
            self.update_data_table()
        else:
            self.popout_dialog("Error", "Task edition failed.")

    def update_line_edit(self, row, column):
        self.lineEdit_id.setText(self.tableWidget.item(row, 0).text())
        self.lineEdit_summary.setText(self.tableWidget.item(row, 1).text())
    
    def update_data_table(self):
        # Query the latest task data of Jira project
        self.jira.tasks = self.jira.query_tasks()
        if self.jira.tasks == False:
            self.popout_dialog("Error", "Something wrong while communicating with Jira. Please check jira_config.json.")
            return
        task_by_assignee = self.jira.filter_task_by_assignee(self.account_config["name"])

        # Remove existing data
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(0)

        # Set table row and column
        self.tableWidget.setRowCount(len(task_by_assignee))
        self.tableWidget.setColumnWidth(0, 75)
        self.tableWidget.setColumnWidth(1, 330)
        self.tableWidget.setColumnWidth(2, 75)
        self.tableWidget.setColumnWidth(3, 90)
        self.tableWidget.setColumnWidth(4, 95)
        self.tableWidget.setColumnWidth(5, 80)
        
        # Fill in data
        id = 0
        for key in task_by_assignee:
            self.add_data_table(
                id, 
                key,
                self.jira.tasks[key]["summary"],
                self.jira.tasks[key]["status"],
                self.jira.tasks[key]["dueDate"],
                self.jira.tasks[key]["estimate"],
                self.jira.tasks[key]["timeSpent"]
            )
            id = id + 1
    
    def add_data_table(self, row, key, summary, status, due_date, estimate, time_spent):
        key_item = QTableWidgetItem(key)
        summary_item = QTableWidgetItem(summary)
        status_item = QTableWidgetItem(status)
        due_item = QTableWidgetItem(due_date)
        estimate_item = QTableWidgetItem(self.convert_hour_to_day_hour(estimate))
        time_spent = QTableWidgetItem(self.convert_hour_to_day_hour(time_spent))

        self.tableWidget.setItem(row, 0, key_item)
        self.tableWidget.setItem(row, 1, summary_item)
        self.tableWidget.setItem(row, 2, status_item)
        self.tableWidget.setItem(row, 3, due_item)
        self.tableWidget.setItem(row, 4, estimate_item)
        self.tableWidget.setItem(row, 5, time_spent)

    def convert_hour_to_day_hour(self, hour):
        if hour == "":
            return ""
        day_string = ""
        if hour // 8 != 0:
            day_string = str(hour // 8) + " days "
        hour_string = ""
        if hour % 8 != 0:
            hour_string = str(hour % 8) + " hours "
        return day_string + hour_string

    def popout_dialog(self, title, message):
        dialog = QMessageBox()
        dialog.setWindowTitle(title)
        dialog.setText(message)
        if title == "Error":
            dialog.setIcon(QMessageBox.Icon.Warning)
        elif title == "Success":
            dialog.setIcon(QMessageBox.Icon.Information)
        dialog.exec()


class CustomDelegate(QStyledItemDelegate):
    def __init__(self, parent, jira):
        super().__init__(parent)
        self.jira = jira

    def createEditor(self, parent, option, index):
        if index.column() == 0: # Task ID
            self.popout_dialog("Error", "Task ID cannot be changed.")
            return
        elif index.column() == 1: # Summary
            editor = QLineEdit(parent)
            editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
            return editor
        elif index.column() == 2: # Status
            editor = QComboBox(parent)
            for status in self.jira.statuses:
                editor.addItem(status)
            return editor
        elif index.column() == 3: # Due Date
            self.popout_dialog("Error", "Due Date cannot be changed.")
            return
        elif index.column() == 4: # Estimate
            self.popout_dialog("Error", "Estimate cannot be changed.")
            return
        elif index.column() == 5: # Time Spent
            self.popout_dialog("Error", "Time Spent cannot be changed.")
            return
        else:
            return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        if isinstance(editor, QLineEdit):
            editor.setText(index.data(Qt.ItemDataRole.DisplayRole))
        elif isinstance(editor, QComboBox):
            editor.setCurrentText(index.data(Qt.ItemDataRole.DisplayRole))
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        row = index.row()
        column = index.column()
        task_key = self.parent().item(row, 0).text()

        if isinstance(editor, QLineEdit):
            # Summary
            if column == 1: 
                if len(editor.text()) <= 0:
                    self.popout_dialog("Error", "Summary cannot be empty.")
                    return
                check = self.jira.edit_task(task_key, "summary", editor.text())
                if check:
                    self.popout_dialog("Success", "Task edited successfully!")
                    model.setData(index, editor.text(), Qt.ItemDataRole.EditRole)
                else:
                    self.popout_dialog("Error", "Task edition failed.")
        elif isinstance(editor, QComboBox):
            # Status
            if column == 2:
                # Fix "To Do" and "Backlog" switch issue
                status_input = editor.currentText()
                if status_input == "To Do":
                    status_input = "Backlog"
                elif status_input == "Backlog":
                    status_input = "To Do"
                
                check = self.jira.edit_task(task_key, "status", status_input)
                if check:
                    self.popout_dialog("Success", "Task edited successfully!")
                    model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)
                else:
                    self.popout_dialog("Error", "Task edition failed.")
        else:
            super().setModelData(editor, model, index)

    def popout_dialog(self, title, message):
        dialog = QMessageBox()
        dialog.setWindowTitle(title)
        dialog.setText(message)
        if title == "Error":
            dialog.setIcon(QMessageBox.Icon.Warning)
        elif title == "Success":
            dialog.setIcon(QMessageBox.Icon.Information)
        dialog.exec()



