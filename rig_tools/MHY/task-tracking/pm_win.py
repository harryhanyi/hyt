import os
import sys
import re
import json
from datetime import date
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QTableWidget, QTableWidgetItem, QMenu, QComboBox, QLineEdit, QStyledItemDelegate
from PyQt6.QtGui import QAction
from PyQt6 import uic

from jira_util import JiraUtil


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class PMWin(QMainWindow):
    def __init__(self):
        super().__init__()

        ###############################################################################
        # Set up Jira
        try:
            with open(BASE_DIR+"/jira_config.json", "r") as file:
                jira_config = json.load(file)
        except FileNotFoundError:
            print(f"File not found: jira_config.json")
        except json.JSONDecodeError:
            print(f"Invalid JSON format in file: jira_config.json")
        except Exception as e:
            print(f"Error occurred while reading jira_config.json: {str(e)}")


        self.jira = JiraUtil(
            jira_config["base_url"], 
            jira_config["admin_email"], 
            jira_config["admin_token"], 
            jira_config["project_key"],
            jira_config["pm"]
        )

        ###############################################################################
        # Load ui file
        uic.loadUi(BASE_DIR+"/pm_win.ui", self)

        # Connect signals and slots
        self.button_create.clicked.connect(self.create_task)
        self.button_edit.clicked.connect(self.edit_estimate)
        self.tableWidget.cellClicked.connect(self.update_line_edit)

        # Fill ui data
        self.fill_data_assignee()
        self.update_data_table()
        self.lineEdit_dueDate.setText(date.today().strftime("%Y-%m-%d"))

        # Set up tableWidget context menu for task deleting
        self.tableWidget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tableWidget.customContextMenuRequested.connect(self.show_context_menu_table)

        # Set up tableWidget custom delegate for task editing
        delegate = CustomDelegate(self.tableWidget, self.jira)
        self.tableWidget.setItemDelegate(delegate)

    def edit_estimate(self):
        # Check if any task is selected
        task_key = self.lineEdit_id.text()
        if len(task_key) <= 0:
            self.popout_dialog("Error", "Please select one task in the table to continue.")
            return

        # Check if time input is valid
        estimate_day_test = self.lineEdit_estimate_edit_day.text()
        estimate_hour_test = self.lineEdit_estimate_edit_hour.text()
        if len(estimate_day_test) <= 0 or len(estimate_hour_test) <= 0:
            self.popout_dialog("Error", "Estimate cannot be empty.")
            return
        try:
            estimate_day_int = int(estimate_day_test)
            estimate_hour_int = int(estimate_hour_test)
        except ValueError:
            self.popout_dialog("Error", "Estimate needs to be integer.")
            return

        # Convert day-hour into hour unit
        estimate_hour_int = int(estimate_day_test) * 8 + int(estimate_hour_test)

        # Send data to Jira
        check = self.jira.edit_task(task_key, "estimate", str(estimate_hour_int))
        if check:
            self.popout_dialog("Success", "Estimate edited successfully!")
            self.update_data_table()
        else:
            self.popout_dialog("Error", "Estimate edition failed.")

    def delete_task(self):
        selected_item = self.tableWidget.currentItem()
        if selected_item is not None:
            check = self.jira.delete_task(self.tableWidget.item(selected_item.row(), 0).text())
            if check:
                self.popout_dialog("Success", "Task deleted successfully!")
                self.update_data_table()
            else:
                self.popout_dialog("Error", "Task deletion failed.")

    def create_task(self):
        # Check summary input
        if len(self.lineEdit_summary.text()) <= 0:
            self.popout_dialog("Error", "Summary cannot be empty.")
            self.lineEdit_summary.setText("Here is the summary of new task")
            return

        # Check due date input
        pattern = r'^\d{4}-\d{2}-\d{2}$'
        if len(self.lineEdit_dueDate.text()) <= 0 or not re.match(pattern, self.lineEdit_dueDate.text()):
            self.popout_dialog("Error", "Due date cannot be empty and needs to be YYYY-MM-DD.")
            self.lineEdit_dueDate.setText(date.today().strftime("%Y-%m-%d"))
            return

        # Check estimate input
        if len(self.lineEdit_estimate_new_day.text()) <= 0 or \
            not self.lineEdit_estimate_new_day.text().isdigit() or \
            len(self.lineEdit_estimate_new_hour.text()) <= 0 or \
            not self.lineEdit_estimate_new_hour.text().isdigit():
            self.popout_dialog("Error", "Estimate cannot be empty and needs to be number.")
            self.lineEdit_estimate_new_day.setText("0")
            self.lineEdit_estimate_new_hour.setText("0")
            return

        check = self.jira.create_task(
                    self.lineEdit_summary.text(), 
                    self.lineEdit_dueDate.text(),
                    self.convert_day_hour_to_hour(self.lineEdit_estimate_new_day.text(), self.lineEdit_estimate_new_hour.text()),
                    self.comboBox_assignee.currentText()
                )
        if check:
            self.popout_dialog("Success", "Task created successfully!")
            self.update_data_table()
        else:
            self.popout_dialog("Error", "Task creation failed.")

    def convert_day_hour_to_hour(self, day_string, hour_string):
        return str(int(day_string) * 8 + int(hour_string))

    def popout_dialog(self, title, message):
        dialog = QMessageBox()
        dialog.setWindowTitle(title)
        dialog.setText(message)
        if title == "Error":
            dialog.setIcon(QMessageBox.Icon.Warning)
        elif title == "Success":
            dialog.setIcon(QMessageBox.Icon.Information)
        dialog.exec()

    def fill_data_assignee(self):
        if self.jira.assignees == False:
            self.popout_dialog("Error", "Something wrong while communicating with Jira. Please check jira_config.json.")
            return

        # Update ui data
        for name in self.jira.assignees:
            self.comboBox_assignee.addItem(name)

    def update_line_edit(self, row, column):
        self.lineEdit_id.setText(self.tableWidget.item(row, 0).text())
        self.lineEdit_summary.setText(self.tableWidget.item(row, 1).text())
        estimate_day, estimate_hour = self.separate_day_hour(self.tableWidget.item(row, 4).text())
        self.lineEdit_estimate_edit_day.setText(estimate_day)
        self.lineEdit_estimate_edit_hour.setText(estimate_hour)

    def separate_day_hour(self, time):
        if time == "":
            return "0", "0"
        items = time.split()
        if len(items) == 4:
            return items[0], items[2]
        if items[1] == "days":
            return items[0], "0"
        return "0", items[0]

    def update_data_table(self):
        # Query the latest task data of Jira project
        self.jira.tasks = self.jira.query_tasks()
        if self.jira.tasks == False:
            self.popout_dialog("Error", "Something wrong while communicating with Jira. Please check jira_config.json.")
            return

        # Remove existing data
        self.tableWidget.clearContents()
        self.tableWidget.setRowCount(0)

        # Set table row and column
        self.tableWidget.setRowCount(len(self.jira.tasks))
        self.tableWidget.setColumnWidth(0, 75)
        self.tableWidget.setColumnWidth(1, 230)
        self.tableWidget.setColumnWidth(2, 75)
        self.tableWidget.setColumnWidth(3, 90)
        self.tableWidget.setColumnWidth(4, 95)
        self.tableWidget.setColumnWidth(5, 100)
        self.tableWidget.setColumnWidth(6, 80)
        
        # Fill in data
        id = 0
        for key in self.jira.tasks:
            self.add_data_table(
                id, 
                key,
                self.jira.tasks[key]["summary"],
                self.jira.tasks[key]["status"],
                self.jira.tasks[key]["dueDate"],
                self.jira.tasks[key]["estimate"],
                self.jira.tasks[key]["timeSpent"],
                self.jira.tasks[key]["assignee"]
            )
            id = id + 1

    def add_data_table(self, row, key, summary, status, due_date, estimate, time_spent, assignee):
        key_item = QTableWidgetItem(key)
        summary_item = QTableWidgetItem(summary)
        status_item = QTableWidgetItem(status)
        due_item = QTableWidgetItem(due_date)
        estimate_item = QTableWidgetItem(self.convert_time_to_string(estimate))
        time_spent = QTableWidgetItem(self.convert_time_to_string(time_spent))
        assignee_item = QTableWidgetItem(assignee)

        self.tableWidget.setItem(row, 0, key_item)
        self.tableWidget.setItem(row, 1, summary_item)
        self.tableWidget.setItem(row, 2, status_item)
        self.tableWidget.setItem(row, 3, due_item)
        self.tableWidget.setItem(row, 4, estimate_item)
        self.tableWidget.setItem(row, 5, time_spent)
        self.tableWidget.setItem(row, 6, assignee_item)        

    def convert_time_to_string(self, hour):
        if hour == "":
            return ""
        day_string = ""
        if hour // 8 != 0:
            day_string = str(hour // 8) + " days "
        hour_string = ""
        if hour % 8 != 0:
            hour_string = str(hour % 8) + " hours "
        return day_string + hour_string

    def show_context_menu_table(self, position):
        selected_item = self.tableWidget.currentItem()
        if selected_item is not None:
            context_menu = QMenu(self)
            delete_action = QAction("Delete this task", self)
            delete_action.triggered.connect(self.delete_task)
            context_menu.addAction(delete_action)
            context_menu.exec(self.tableWidget.mapToGlobal(position))


class CustomDelegate(QStyledItemDelegate):
    def __init__(self, parent, jira):
        super().__init__(parent)
        self.jira = jira

    def createEditor(self, parent, option, index):
        if index.column() == 0: # Task ID
            self.popout_dialog("Error", "Task ID cannot be changed.")
            return
        elif index.column() in [1, 3]:
            editor = QLineEdit(parent)
            editor.setAlignment(Qt.AlignmentFlag.AlignCenter)
            return editor
        elif index.column() == 2: # Status
            editor = QComboBox(parent)
            for status in self.jira.statuses:
                editor.addItem(status)
            return editor
        elif index.column() == 4: # Estimate
            self.popout_dialog("Error", "Please change Estimate in section of Edit Estimate below.")
            return
        elif index.column() == 5: # Time Spent
            self.popout_dialog("Error", "Time Spent cannot be changed.")
            return
        elif index.column() == 6: # Assignee
            editor = QComboBox(parent)
            for assignee in self.jira.assignees:
                editor.addItem(assignee)
            return editor
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
            
            # Due Date
            elif column == 3:
                pattern = r'^\d{4}-\d{2}-\d{2}$'
                if len(editor.text()) <= 0 or not re.match(pattern, editor.text()):
                    self.popout_dialog("Error", "Due date cannot be empty and needs to be YYYY-MM-DD.")
                    return
                check = self.jira.edit_task(task_key, "duedate", editor.text())
                if check:
                    self.popout_dialog("Success", "Task edited successfully!")
                    model.setData(index, editor.text(), Qt.ItemDataRole.EditRole)
                else:
                    self.popout_dialog("Error", "Task edition failed.")   

        elif isinstance(editor, QComboBox):
            # Assignee
            if column == 6:
                check = self.jira.edit_task(task_key, "assignee", editor.currentText())
                if check:
                    self.popout_dialog("Success", "Task edited successfully!")
                    model.setData(index, editor.currentText(), Qt.ItemDataRole.EditRole)
                else:
                    self.popout_dialog("Error", "Task edition failed.")
            
            # Status
            elif column == 2:
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

