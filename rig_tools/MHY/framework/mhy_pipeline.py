import sys
import win32gui
import win32con
import win32api
import win32gui_struct
import ctypes
import json
import datetime
import time
import subprocess
import threading
import os
import tempfile
import psutil


DOCUMENTS_DIR = os.path.expanduser("~\Documents")
MHY_DIR = DOCUMENTS_DIR + "/MHY"
BASE_DIR = DOCUMENTS_DIR + "/MHY/framework"
TEMP_DIR = tempfile.gettempdir()


class Runner:
    def __init__(self, icon, tooltip, menu_options):
        self.icon = icon
        self.tooltip = tooltip
        self.menu_options = menu_options
        self._message_map = {
            win32con.WM_DESTROY: self.on_destroy,
            win32con.WM_COMMAND: self.on_command,
            win32con.WM_USER+20: self.on_taskbar_notify
        }
        
        # Read Config.json
        self.config = self.read_config(BASE_DIR+"/config.json")
        if not self.config:
            return
        self.current_version = self.config['version_number']
        self.tooltip = self.tooltip + ' v' + self.current_version

        # Exit if a same process already exists
        self.check_if_same_process_exist(self.config['runner_name'])

        # Register the window class
        wc = win32gui.WNDCLASS()
        hinst = wc.hInstance = win32api.GetModuleHandle(None)
        wc.lpszClassName = 'PythonTaskbar'
        wc.lpfnWndProc = self._message_handler
        class_atom = win32gui.RegisterClass(wc)

        # Create the window
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = win32gui.CreateWindow(class_atom, 'Taskbar', style,
                                          0, 0, win32con.CW_USEDEFAULT,
                                          win32con.CW_USEDEFAULT, 0, 0,
                                          hinst, None)
        win32gui.UpdateWindow(self.hwnd)
        self.notify_id = None
        self.refresh_icon()

        # Start a timer
        self.timer = None
        self.start_timer()

        # Check version change
        self.check_if_version_change()

    def start_timer(self):
        self.timer = threading.Timer(self.config['update_interval'], self.check_for_update)
        self.timer.daemon = True  # Set the thread as a daemon to exit with the main thread
        self.timer.start()

    def check_for_update(self):
        # # Check if today is Sunday and the last update date is different from today
        # today = datetime.date.today()
        # last_update_date = datetime.datetime.strptime(self.config["last_update"], "%Y-%m-%d").date()
        # if today.weekday() == 6 and today != last_update_date:
        #     subprocess.run(["python", "mhy_updater.py"])

        print("Run updater.py")
        # subprocess.run(["python", "mhy_updater.py"])
        subprocess.run("mhy_updater.exe", check=True)

        # Show notification of version change
        # self.show_notification()

        # Restart the timer for the next check
        self.start_timer()

    def refresh_icon(self):
        # Load the icon and add to the system tray
        hicon = win32gui.LoadImage(0, self.icon, win32con.IMAGE_ICON,
                                   0, 0, win32con.LR_LOADFROMFILE)
        if self.notify_id:
            message = win32gui.NIM_MODIFY
        else:
            message = win32gui.NIM_ADD
        self.notify_id = (self.hwnd, 0, win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP, win32con.WM_USER+20, hicon, self.tooltip)
        win32gui.Shell_NotifyIcon(message, self.notify_id)

    def on_destroy(self, hwnd, msg, wparam, lparam):
        nid = (self.hwnd, 0)
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
        win32gui.PostQuitMessage(0)

    def on_command(self, hwnd, msg, wparam, lparam):
        id = win32gui.LOWORD(wparam)
        for option in self.menu_options:
            if id == option[0]:
                option[1]()

    def on_taskbar_notify(self, hwnd, msg, wparam, lparam):
        if lparam == win32con.WM_LBUTTONUP:
            pass  # Single-click event handling
        elif lparam == win32con.WM_LBUTTONDBLCLK:
            pass  # Double-click event handling
        elif lparam == win32con.WM_RBUTTONUP:
            self.show_menu()
        return True

    def show_menu(self):
        menu = win32gui.CreatePopupMenu()
        for option in self.menu_options:
            win32gui.AppendMenu(menu, win32con.MF_STRING, option[0], option[2])
        pos = win32gui.GetCursorPos()
        win32gui.SetForegroundWindow(self.hwnd)
        win32gui.TrackPopupMenu(menu, win32con.TPM_LEFTALIGN, pos[0], pos[1], 0, self.hwnd, None)
        win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)

    def _message_handler(self, hwnd, msg, wparam, lparam):
        if msg == win32con.WM_CREATE:
            self.hinst = win32gui_struct.HMODULE(ctypes.windll.kernel32.GetModuleHandle(None))
            return 0
        if msg == win32con.WM_DESTROY:
            self.on_destroy(hwnd, msg, wparam, lparam)
        elif msg == win32con.WM_COMMAND:
            self.on_command(hwnd, msg, wparam, lparam)
        elif msg == win32con.WM_USER+20:
            self.on_taskbar_notify(hwnd, msg, wparam, lparam)
        else:
            return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
        return 0

    def read_config(self, path):
        try:
            with open(path, "r") as file:
                return json.load(file)
        except FileNotFoundError:
            print("config path: "+BASE_DIR+"/config.json")
            print(f"File not found: config.json")
            return None
        except json.JSONDecodeError:
            print(f"Invalid JSON format in file: config.json")
            return None
        except Exception as e:
            print(f"Error occurred while reading config.json: {str(e)}")
            return None

    def show_notification(self):
        print("show notification")
        # Check new version number in config
        self.config = self.read_config(BASE_DIR+"/config.json")
        if not self.config:
            print("not self.config")
            return
        new_version = self.config['version_number']
        if not new_version or int(new_version) <= int(self.current_version):
            print("new_version not or less")
            return
        message = f"Version Updated: v{self.current_version} -> v{new_version}"
        title = "MHY Pipeline Update"
        duration = 5
        win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, (self.hwnd, 0, win32gui.NIF_INFO, win32con.WM_USER + 20, 0, "", message, duration * 1000, "", win32gui.NIIF_INFO))
        self.current_version = new_version   

    def check_if_same_process_exist(self, name):
        process_count = 0
        for process in psutil.process_iter(['pid', 'name']):
            if process.info['name'] == name:
                process_count = process_count + 1
        print('runner process count: '+str(process_count))
        if process_count > 1 * 2:
            sys.exit(0)
    
    def check_if_version_change(self):
        # Check mhy_pipeline.json in temp folder

        # Create mhy_pipeline.json if it doesn't exist or cannot be read
        mhy_json_dir = TEMP_DIR + "/mhy_pipeline.json"
        if not os.path.exists(mhy_json_dir) or not self.read_config(mhy_json_dir):
            print("mhy_pipeline.JSON doesn't exist or cannot be read")
            self.previous_version = self.current_version
            data = {"version_number": self.current_version}
            with open(mhy_json_dir, 'w') as file:
                json.dump(data, file)            
        else:
            env_json = self.read_config(mhy_json_dir)
            self.previous_version = env_json['version_number']
            # if int(self.previous_version) < int(self.current_version):
            if self.previous_version != self.current_version:
                print("Version changes")
                
                # Show notification of version change
                message = f"Version Updated: v{self.previous_version} -> v{self.current_version}"
                title = "MHY Pipeline Update"
                duration = 5
                win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, (self.hwnd, 0, win32gui.NIF_INFO, win32con.WM_USER + 20, 0, "", message, duration * 1000, "", win32gui.NIIF_INFO))
                
                # Update mhy_pipeline.json with new version
                self.previous_version = self.current_version
                data = {"version_number": self.current_version}
                with open(mhy_json_dir, 'w') as file:
                    json.dump(data, file)


if __name__ == "__main__":
    icon_path = BASE_DIR + '/mi.ico'
    tooltip_text = 'MHY Pipeline'
    menu_options = [
        (1, lambda: subprocess.run(["python", MHY_DIR+"/framework/mhy_win.py"]), "Open UI"),
        # (1, lambda: subprocess.run(["python", "E:/github/mhy_launcher/core/framework/mhy_win.py"]), "Open UI"),
        (2, lambda: sys.exit(), "Exit")
    ]

    # Create the Runner instance and assign it to a global variable
    sys_runner = Runner(icon_path, tooltip_text, menu_options)

    # Run the application event loop
    win32gui.PumpMessages()

