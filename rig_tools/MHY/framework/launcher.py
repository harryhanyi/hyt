import os
import shutil
import subprocess
import psutil
import datetime
import json
import time


DEST_DIR = os.path.expanduser("~\Documents")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Launcher:
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

    def launch(self):
        # Replace old files with new ones
        print("replace files")
        dest_dir = f"{DEST_DIR}/{self.config['base_folder']}"
        print("dest_dir: " + dest_dir)
        if os.path.exists(dest_dir):
            try:
                shutil.rmtree(dest_dir)
                # os.rmdir(dest_dir)
            except OSError as e:
                print(f"Error while removing folder: {e}")
                return
        src_dir = os.path.dirname(BASE_DIR)
        print("src_dir: " + src_dir)
        shutil.copytree(src_dir, dest_dir)

        # Run mhy_pipeline.exe in Documents folder
        print("run runner")
        # runner_path = os.path.join(dest_dir, "\\framework\\mhy_pipeline.exe")
        runner_path = dest_dir + "/framework/mhy_pipeline.exe"
        print("runner path: " + runner_path)
        subprocess.run(runner_path)

        print("Launcher exits")
        return


if __name__ == "__main__":
    launcher = Launcher()
    launcher.launch()

