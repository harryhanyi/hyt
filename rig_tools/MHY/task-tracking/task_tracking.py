import os
import sys
import json
from PyQt6.QtWidgets import QApplication

from email_win import EmailWin
from pm_win import PMWin
from member_win import MemberWin


BASE_DIR = os.path.dirname(os.path.abspath(__file__))


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Check if account role exists
    try:
        with open(BASE_DIR+"/account_config.json", "r") as file:
            account_config = json.load(file)
    except FileNotFoundError:
        print(f"File not found: account_config.json")
    except json.JSONDecodeError:
        print(f"Invalid JSON format in file: account_config.json")
    except Exception as e:
        print(f"Error occurred while reading account_config.json: {str(e)}")


    # If no, ask user to type in email then decide role based on email
    if len(account_config["role"]) <= 0:
        emailWin = EmailWin()
        emailWin.show()
    
    # If yes, Show client window based on role
    else:
        if account_config["role"] == "pm":
            client = PMWin()
            client.show()
        else:
            client = MemberWin()
            client.show()

    sys.exit(app.exec())
