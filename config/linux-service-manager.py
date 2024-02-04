import os
import platform
from pathlib import Path
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
    # ~/.config/systemd/user.control/* - one user directory where systemd 'unit files' are stored
    #NOTE this means we don't have to use admin privileges to access the non-user filesystem

    def __init__(self):
        self.operating_sys = platform.system().lower()
        if self.operating_sys != "linux":
            raise OSError("This manager is only compatible with Linux systems.")
        if not self.isInProjectRoot():
            raise FileNotFoundError("This script was not executed in the Parkbot root directory.")


    def findJava(self) -> Path | None:
        """Searches through a user's home directory given their operating system. On windows, also attempts to find an executable "java.exe" that exists under a parent directory which indicates it is jre 17."""
        desired_file = "java"
        user = os.getlogin()
        dirs_to_search = [Path("~/")] # the external dep setup downloads java to the home directory, and we check 
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

    def _findBotPy(self) -> Path | None:
        """Searches ParkBot's directory for the 'bot.py' file, and returns its path as a Path object."""
        desired_file = "bot.py"
        parkbot_dir = Path(os.getcwd())
        for dirpath, dirs, files in os.walk(parkbot_dir):
            for filename in files:
                if (desired_file == filename):
                    return Path(dirpath).absolute() / desired_file
        return None
    
    def findLavalinkJar(self) -> Path | None:
        desired_file = "lavalink.jar"
        dirs_to_search = [Path("~/")]
        for directory in dirs_to_search:
            for dirpath, dirs, files in os.walk(directory):
                for filename in files:
                    if (desired_file == filename):
                        return Path(dirpath) / desired_file
        return None
    
    def isInProjectRoot(self) -> bool:
        """Checks if the terminal is in the ParkBot root directory."""
        here = Path(os.getcwd())
        root_components = {"cogs", "data"}
        sub_dirs = set([x.name for x in here.iterdir() if x.is_dir()])
        intersection = sub_dirs.intersection(root_components)
        if root_components == intersection:
            return True
        return False
    
    def generate_parkbot_service_file(self) -> None:
        parkbot_root = Path(os.getcwd())
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
            "ExecStart": f"/usr/bin/python3 {parkbot_root}/bot.py",
            "Restart": "on-failure",
            "RestartSec": "10",
        }
        parkbot_service_path = "/etc/systemd/system/parkbot.service"
        with open(parkbot_service_path, "w") as file:
            config.write(file)
        

    def generate_lavalink_service_file(self) -> None:
        parkbot_root = Path(os.getcwd())
        lavalink_jar = self.findLavalinkJar() # both of these should 
        java = self.findJava()
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
        lavalink_service_path = "/etc/systemd/system/lavalink.service"
        with open(lavalink_service_path, "w") as file:
            config.write(file)

    

if __name__ == "__main__":
    service_manager = LinuxServiceManager()
    service_manager.generate_lavalink_service_file()
    service_manager.generate_parkbot_service_file()    