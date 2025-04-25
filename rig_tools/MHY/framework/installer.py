import os
import shutil
import subprocess
import psutil
import datetime
import json
import time
import win32com.client


DEST_DIR = os.path.expanduser("~\Documents")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Installer:
    def __init__(self):

        # Read Config JSON
        self.config = None
        try:
            with open(BASE_DIR + "\config.json", "r") as file:
                self.config = json.load(file)
        except FileNotFoundError:
            print(f"File not found: config.json")
        except json.JSONDecodeError:
            print(f"Invalid JSON format in file: config.json")
        except Exception as e:
            print(f"Error occurred while reading config.json: {str(e)}")

    def install(self):
        # Kill existing processes
        print("kill processes")
        self.kill_process_by_name(self.config['runner_name'])
        self.kill_process_by_name(self.config['updater_name'])
        time.sleep(1)

        # Unset read-only
        dest_dir = f"{DEST_DIR}/{self.config['base_folder']}"
        print("dest_dir: " + dest_dir)
        try:
            # Iterate through all files and directories in the given path and its subdirectories
            print("unset read-only")
            for root, dirs, files in os.walk(dest_dir):
                for d in dirs:
                    dir_path = os.path.join(root, d)
                    os.chmod(dir_path, 0o755)  # Unset read-only attribute for directories

                for f in files:
                    file_path = os.path.join(root, f)
                    os.chmod(file_path, 0o644)  # Unset read-only attribute for files
        except Exception as e:
            print(f"Error occurred while unsetting read-only: {str(e)}")
        
        # Replace old files with new ones
        print("replace files")
        if os.path.exists(dest_dir):
            try:
                shutil.rmtree(dest_dir)
            except OSError as e:
                print(f"Error while removing folder: {e}")
                return
        src_dir = os.path.dirname(BASE_DIR)
        print("src_dir: " + src_dir)
        shutil.copytree(src_dir, dest_dir)

        # Create a short-cut and add it to Desktop
        runner_path = dest_dir + "/framework/mhy_pipeline.exe"
        icon_path = dest_dir + "/framework/mi.ico"
        self.add_shortcut_to_desktop(runner_path, icon_path)

        # Run mhy_pipeline.exe in Documents folder
        subprocess.run(runner_path)

        print("Installer exits")
        return
    
    def kill_process_by_name(self, name):
        for process in psutil.process_iter(['pid', 'name']):
            if process.info['name'] == name:
                process.kill()

    def add_shortcut_to_desktop(self, target_path, icon_path):
        # Create a short cut to mhy_pipeline.exe in Documents\MHY
        desktop_dir = os.path.expanduser("~\Desktop")
        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(desktop_dir+'/MHY_Pipeline.lnk')
        shortcut.Targetpath = target_path
        if icon_path:
            shortcut.IconLocation = icon_path
        shortcut.save()


if __name__ == "__main__":
    installer = Installer()
    installer.install()

