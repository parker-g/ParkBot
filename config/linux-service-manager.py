import os
import getpass
import platform
import subprocess
from pathlib import Path
from subprocess import PIPE
from configparser import ConfigParser

acceptable_javas = {
    "jdk-17",
    "openlogic-openjdk-jre-17",
    "openjdk-jre-17",
    "openjdk-jdk-17",
    "openjdk-17-jdk",
    "openjdk-17-jre",
}

#NOTE this class requries elevated privileges to work
class LinuxServiceManager:

    def is_in_project_root(self) -> bool:
        """Checks if the terminal is in the ParkBot root directory."""
        here = Path(os.getcwd())
        root_components = {"cogs", "data"}
        sub_dirs = set([x.name for x in here.iterdir() if x.is_dir()])
        intersection = sub_dirs.intersection(root_components)
        if root_components == intersection:
            return True
        return False
    
    def find_python(self) -> Path | None:
        """Returns the path to the python executable in a virtual environment, on linux machines."""
        parkbot_root = Path(os.getcwd())
        desired_file = "python"
        for dirpath, dirs, files in os.walk(parkbot_root):
            for filename in files:
                if (filename == desired_file):
                    if os.access(Path(dirpath) / filename, os.X_OK):
                        return Path(dirpath) / desired_file
        return None    
    
    def __init__(self):
        self.password = getpass.getpass("Please enter your linux user password:")
        self.operating_sys = platform.system().lower()
        if self.operating_sys != "linux":
            raise OSError("This manager is only compatible with Linux systems.")
        if not self.is_in_project_root():
            raise FileNotFoundError("This script was not executed in the Parkbot root directory.")

    def find_java(self) -> Path | None:
        """Searches through a user's home directory given their operating system. On windows, also attempts to find an executable "java.exe" that exists under a parent directory which indicates it is jre 17."""
        desired_file = "java"
        user = getpass.getuser()
        dirs_to_search = [Path(f"/home/{user}")] # the external dep setup downloads java to the home directory, and we check 
        for directory in dirs_to_search:
            try:
                for dirpath, dirs, files in os.walk(directory):
                    for filename in files:
                        if (desired_file == filename):
                            this_java = Path(dirpath) / desired_file
                            if os.access(this_java, os.X_OK) and this_java.parent.parent.name in acceptable_javas:
                                return Path(dirpath) / desired_file
            except PermissionError:
                print(f"---------------------------\nUnable to search Program Files directory. Searching {user}'s home directory.\n---------------------------")
                continue
        return None

    def find_lavalink_jar(self) -> Path | None:
        desired_file = "lavalink.jar"
        user = getpass.getuser()
        dirs_to_search = [Path(f"/home/{user}")]
        for directory in dirs_to_search:
            for dirpath, dirs, files in os.walk(directory):
                for filename in files:
                    if (desired_file == filename):
                        return Path(dirpath) / desired_file
        return None

    def generate_parkbot_service_file(self) -> None:
        parkbot_root = Path(os.getcwd())
        parkbot_python = self.find_python()
        config = ConfigParser()
        config.optionxform = str # preserve case
        config["Unit"] = {
            "Description": "A Discord bot service, bringing music and games to guilds it serves.",
            "Before": "lavalink.service",
            "Requires": "lavalink.service",
        }
        config["Service"] = {
            "Type": "exec",
            "WorkingDirectory": f"{parkbot_root}",
            "ExecStart": f"{parkbot_python} {parkbot_root}/bot.py",
            "Restart": "on-failure",
            "RestartSec": "10",
        }

        temp_dir = parkbot_root / "parkbot.service"
        parkbot_service_path = Path("/etc/systemd/system/parkbot.service")
        with open(temp_dir, "w") as file:
            config.write(file)
        process = subprocess.Popen(["sudo", "mv", str(temp_dir), str(parkbot_service_path)], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        process.communicate(self.password.encode())
        process.wait()

    def generate_lavalink_service_file(self) -> None:
        parkbot_root = Path(os.getcwd())
        lavalink_jar = self.find_lavalink_jar() # both of these should 
        java = self.find_java()
        if not lavalink_jar or not java:
            raise FileNotFoundError("Failed to create lavalink.service file. Could not find either `lavalink.jar` or the java 17 executable in this user's home directory.")
        config = ConfigParser()
        config.optionxform = str # preserve case
        config["Unit"] = {
            "Description": "Node for serving music to Discord",
        }
        config["Service"] = {
            "Type": "exec",
            "ExecStart": f"{java} -jar {lavalink_jar}",
            "Restart": "on-failure",
            "RestartSec": "10",
        }
        
        temp_dir = parkbot_root / "lavalink.service"
        lavalink_service_path = Path("/etc/systemd/system/lavalink.service")
        with open(temp_dir, "w") as file:
            config.write(file)
        process = subprocess.Popen(["sudo", "mv", str(temp_dir), str(lavalink_service_path)], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        process.communicate(self.password.encode())
        process.wait()

    def enable_parkbot_service(self) -> None:
        process = subprocess.Popen(["sudo", "systemctl", "enable", "parkbot.service"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        process.communicate(self.password.encode())
        return_code = process.wait()
        match return_code:
            case 0: # success
                print("Enabled parkbot.service.")
            case 1:
                print("Failed to enable parkbot.service.")
            case _:
                print("Failed to enable parkbot.service; unhandled return code.")

    def enable_lavalink_service(self) -> None:
        process = subprocess.Popen(["sudo", "systemctl", "enable", "lavalink.service"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        process.communicate(self.password.encode())
        return_code = process.wait()
        match return_code:
            case 0: # success
                print("Enabled lavalink.service.")
            case 1:
                print("Failed to enable lavalink.service.")
            case _:
                print("Failed to enable lavalink.service; unhandled return code.")

    def generate_all_services(self) -> None:
        self.generate_lavalink_service_file()
        self.generate_parkbot_service_file()
    
    def enable_all_services(self) -> None:
        self.enable_lavalink_service()
        self.enable_parkbot_service()

if __name__ == "__main__":
    service_manager = LinuxServiceManager()
    service_manager.generate_all_services()
    service_manager.enable_all_services()