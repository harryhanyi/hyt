import os
import re
import json
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QTableWidget, QTableWidgetItem, QMenu, QComboBox, QLineEdit, QStyledItemDelegate
from PyQt6.QtGui import QAction
from PyQt6 import uic

from jira_util import JiraUtil
from pm_win import PMWin
from member_win import MemberWin


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class EmailWin(QMainWindow):
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

        uic.loadUi(BASE_DIR+"/email_win.ui", self)
        self.button_submit.clicked.connect(self.submit_email)

    def submit_email(self):
        # Check if input is empty
        email = self.lineEdit_email.text()
        if len(email) <= 0:
            self.popout_dialog("Error", "Email cannot be empty.")
            return

        # Check if input follows email format
        email_pattern = r'^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            self.popout_dialog("Error", "Please input a valid email address.")
            return
        
        # Check if user matches any assignee in the system
        check = False
        names = email.lower().split('@')[0].split('.')
        for assignee in self.jira.assignees:
            assignee_names = assignee.lower().split(' ')
            if names[0] == assignee_names[0] and (len(assignee_names) == 1 or names[1] == assignee_names[1]):
                self.account_config["name"] = assignee
                check = True
        if not check:
            self.popout_dialog("Error", "Cannot find this user in the system. Please try again.")
            return
        
        # Check role based on email
        pm_names = self.account_config["pm"].lower().split(' ')
        if names[0] == pm_names[0] and names[1] == pm_names[1]:
            role = "pm"
        else:
            role = "member"

        # Save role and email to json
        self.account_config["role"] = role
        self.account_config["email"] = email
        with open(BASE_DIR+'/account_config.json', 'w') as file:
            json.dump(self.account_config, file, indent=2)

        # Show client window based on role
        if role == "pm":
            self.client = PMWin()
            self.close()
            self.client.show()
        else:
            self.client = MemberWin()
            self.close()
            self.client.show()

    def popout_dialog(self, title, message):
        dialog = QMessageBox()
        dialog.setWindowTitle(title)
        dialog.setText(message)
        if title == "Error":
            dialog.setIcon(QMessageBox.Icon.Warning)
        elif title == "Success":
            dialog.setIcon(QMessageBox.Icon.Information)
        dialog.exec()
