import requests
import platform
import subprocess
import datetime
import os
import zipfile
import shutil
import tempfile
import urllib.request
import json
import boto3


# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCUMENTS_DIR = os.path.expanduser("~\Documents")
MHY_DIR = DOCUMENTS_DIR + "/MHY"
BASE_DIR = DOCUMENTS_DIR + "/MHY/framework"
TEMP_DIR = tempfile.gettempdir()


class Updater:
    def __init__(self):
        # Read Config JSON
        self.config = None
        try:
            with open(BASE_DIR + "\config.json", "r") as file:
                self.config = json.load(file)
        except FileNotFoundError:
            print(f"File not found: config.json")
            print("config path: " + BASE_DIR + "//config.json")
        except json.JSONDecodeError:
            print(f"Invalid JSON format in file: config.json")
        except Exception as e:
            print(f"Error occurred while reading config.json: {str(e)}")

        self.client_version = self.config['version_number']
        self.server_version = ""
        self.config_url = self.get_aws_url(self.config['server_config'])
        print('config_url: '+self.config_url)
        self.update_url = ""

    def update(self):
        # self.server_version = self.get_server_version(self.config_url)
        if not self.check_if_server_version_is_newer():
        # if not self.server_version or int(self.server_version) <= int(self.client_version):
            print("No need to update")
            return
        print("Need to update")
        self.download_and_run_installer()

    def check_if_server_version_is_newer(self):
        self.server_version = self.get_server_version(self.config_url)

        # Exit if server_version is "0003" or "0004"
        if self.server_version == "0003" or self.server_version == "0004":
            return False

        server_version_list = self.server_version.split(".")
        client_version_list = self.client_version.split(".")
        if int(server_version_list[0]) > int(client_version_list[0]):
            return True
        elif int(server_version_list[0]) == int(client_version_list[0]):
            if int(server_version_list[1]) > int(client_version_list[1]):
                return True
            elif int(server_version_list[1]) == int(client_version_list[1]):
                if int(server_version_list[2]) > int(client_version_list[2]):
                    return True
        return False

    def download_and_run_installer(self):
        # Download the zip file
        self.update_url = self.get_aws_url(self.config['server_update']+self.server_version+self.config['update_ext'])
        print("installer url: " + self.update_url)
        response = requests.get(self.update_url)
        
        # Check if the download was successful
        if response.status_code == 200:
            # Remove the old zip file
            zip_path = os.path.join(TEMP_DIR, self.config['download_file']+self.config['update_ext'])
            if os.path.exists(zip_path):
                os.remove(zip_path)
                print(f"{zip_path} has been deleted.")
            else:
                print(f"{zip_path} does not exist.")
            
            # Save the downloaded zip file
            with open(zip_path, "wb") as file:
                file.write(response.content)
            print("download file")
            
            # Remove the old unzip folder
            extracted_folder = os.path.join(TEMP_DIR, self.config['base_folder'])
            if os.path.exists(extracted_folder):
                try:
                    shutil.rmtree(extracted_folder)
                except OSError as e:
                    print(f"Error while removing folder: {e}")
                    return

            # Unzip the file
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall(extracted_folder)
            print("unzip file")
            
            # Run installer.py from the extracted folder
            # installer_path = os.path.join(extracted_folder, "installer.py")
            installer_path = extracted_folder + "/framework/installer.py"
            print("installer path: " + installer_path)
            subprocess.run(["python", installer_path])

        else:
            print("Failed to download the installer.")

    def get_server_version(self, url):
        try:
            # response = requests.get(f"{self.config['config']}")
            response = requests.get(url)
            if response.status_code == 200:
                server_version = response.json()["version_number"]
                print("Version number from server: " + server_version)
                return server_version
            else:
                print("Cannot query the latest version from the server")
                return None
        except requests.exceptions.RequestException:
            print("Cannot query the latest version from the server")
            return None

    def get_aws_url(self, key):
        s3 = boto3.client(
            's3',
            aws_access_key_id=self.config['aws_access'],
            aws_secret_access_key=self.config['aws_secret']
        )
        expiration_time = 3600  # 1 hour in this example

        # Generate the pre-signed URL
        url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.config['aws_bucket'], 'Key': key},
            ExpiresIn=expiration_time
        )
        return url


if __name__ == "__main__":
    updater = Updater()
    updater.update()
        

