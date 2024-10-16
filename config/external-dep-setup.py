import os
import json
import shutil
import getpass
import platform
import subprocess
import configparser
from enum import Enum
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile
from tarfile import TarFile

import bs4
import yaml
import requests

class ErrorMessage(Enum):
    OS = "The ParkBot setup script is incompatible with this operating system."
    ARCH = "The ParkBot setup script does not include full support for this architecture."


acceptable_javas = {
    "jdk-17",
    "openlogic-openjdk-jre-17",
    "openjdk-jre-17",
    "openjdk-jdk-17",
    "openjdk-17-jdk",
    "openjdk-17-jre",
}

machines = {
    "x64": "AMD64",
    "AMD64": "AMD64",
    "x86_64":  "AMD64",
    "aarch64_be": "arm64",
    "aarch64": "arm64",
    "armv8b": "arm64",
    "armv8l": "arm64",
}

machines_to_github_versions = {
    "64": "AMD64",
    "arm64": "arm64",
}

class JAVA(Enum):
    windows = "java.exe"
    linux = "java"

class FileManager:

    def is_too_deep(self, top_dir:Path, root:str, max_depth:int) -> bool:
        """Function designed to tell os.walk() to stop at a certain depth."""
        starting_len = len(top_dir.parts)
        current_path = Path(root)
        current_path_len = len(current_path.parts)
        return (current_path_len - starting_len > max_depth)

    def walk_to_depth(self, top_dir:Path, depth:int):
        """Generator function - wrapper around os.walk() allowing for a max-depth attribute.\n\nWill walk 'depth' deeper than the given 'top_dir'.\n\nExample: if top_dir = '/home/', and depth = 3, will walk to '/home/foo/bar/foo'."""
        for root, dirs, files in os.walk(top_dir):
            if self.is_too_deep(top_dir, root, depth):
                dirs.clear()
                continue
            yield(root, dirs, files)

class Downloader(FileManager):

    def __init__(self, os:str, machine:str):
        self.operating_sys = os
        self.machine = machine

    def remove_extensions(self, path:Path):
        while path.suffix != "":
            path = path.with_suffix("")
        return path

    #thanks stackoverflow
    def download_url(self, url, download_destination, chunk_size=128) -> None:
        r = requests.get(url, stream=True)
        with open(download_destination, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=chunk_size):
                fd.write(chunk)

    def extract_zip(self, zip_file:Path, unzip_destination:Path) -> None:
        """Extracts and deletes the specified zip archive."""
        zip = ZipFile(zip_file, "r")
        zip.extractall(unzip_destination)
        zip.close()
        os.remove(zip_file)

    def extract_tar(self, tar_file:Path, extract_destination:Path) -> None:
        """Extracts and deletes the specified tar archive."""
        tar = TarFile(tar_file, "r")
        tar.extractall(extract_destination, filter="tar")
        tar.close()
        os.remove(tar_file)

    def extract_gzip(self, tar_file:Path, extract_destination:Path) -> None:
        """Extracts and deletes the specified gzip archive."""
        tar = TarFile.open(tar_file, "r:gz")
        tar.extractall(extract_destination, filter="tar")
        tar.close()
        os.remove(tar_file)

    def extract(self, archive:Path, extract_destination:Path) -> None:
        """Extracts `archive` into `extract_destination`, and deletes `archive`."""
        #BUG stupid ahh design. should be checking the archive file extension
        file_extension = str(archive).split(".")[-1]
        match file_extension:
            case "gz":
                self.extract_gzip(archive, extract_destination)
            case "zip":
                self.extract_zip(archive, extract_destination)
            case "tar":
                self.extract_tar(archive, extract_destination)

    def create_directories(self, path:Path) -> None:
        """Creates the path given if it doesn't already exist."""
        try:
            os.makedirs(path)
        except FileExistsError:
            print("The directory you are trying to create already exists.")
        except PermissionError:
            print("You don't have the permissions to create the Path you provided. Try again with elevated privileges.")

    def move(self, target_current_dir:Path, target_destination_dir:Path) -> None:
        """Moves the target dir to target destination dir. Input absolute paths."""
        os.rename(target_current_dir, target_destination_dir)

class NSSMManager(Downloader):
    """Class responsible for downloading and configuring NSSM, as well as working with Windows services programatically."""

    # https://www.devdungeon.com/content/run-python-script-windows-service - instructions for using nssm after installation
    """Downloads the most recent stable version of NSSM.exe (the non-sucking-service-manager)."""
    def __init__(self, os:str, machine:str):
        super().__init__(os, machine)
        if self.operating_sys != 'windows':
            raise OSError(f"No need to download NSSM on an operating system besides windows.")
    
    def find_nssm(self) -> Path | None:
        """Returns path to "nssm.exe" if it exists in ParkBot directory or user's home directory."""
        user = getpass.getuser()
        parkbot_root = Path(os.getcwd())
        desired_file = "nssm.exe"
        dirs_to_search = [parkbot_root, Path(f"C:/Users/{user}")]
        for dir in dirs_to_search:
            for root, dirs, files in self.walk_to_depth(dir, 5):
                for filename in files:
                    if filename == desired_file and (os.access(Path(root) / filename, os.X_OK)):
                        return Path(root) / filename    
        return None

    def move_nssm(self, nssm_location:Path, final_exe_destination:Path) -> None:
        """Pulls the nssm.exe out from its parent directory + places it in `final_exe_destination`, and deletes all unused source code/ unused exes."""
        nssm_parent_dir = Path(os.getcwd()) / "nssm-2.24"
        os.rename(nssm_location, final_exe_destination / "nssm.exe")
        shutil.rmtree(str(nssm_parent_dir))

    def download_nssm(self, download_dir:Path, extract_destination):
        parkbot_dir = Path(os.getcwd())
        download_url = "https://www.nssm.cc/release/nssm-2.24.zip"
        nssm_destination = download_dir / "nssm.zip"
        self.download_url(download_url, nssm_destination)
        self.extract_zip(nssm_destination, extract_destination)
        nssm_path = self.find_nssm()
        if nssm_path is not None:
            self.move_nssm(nssm_path, parkbot_dir)
        else:
            raise IOError(f"Attempted to download `nssm.exe`, but cannot find it in file system.")

    def _find_python(self) -> Path | None:
        """Searches ParkBot's directory for a python executable and returns the path to it."""
        # since nssm is only used on windows, we can hard code the desired file to have an .exe extension
        desired_file = "python.exe"
        parkbot_dir = Path(os.getcwd())
        for dirpath, dirs, files in os.walk(parkbot_dir):
            for filename in files:
                if (filename == desired_file):
                    return Path(dirpath) / desired_file
        return None
    
    def _find_bot_py(self) -> Path | None:
        """Searches ParkBot's directory for the 'bot.py' file, and returns its path as a Path object."""
        desired_file = "bot.py"
        parkbot_dir = Path(os.getcwd())
        for dirpath, dirs, files in os.walk(parkbot_dir):
            for filename in files:
                if (desired_file == filename):
                    return Path(dirpath).absolute() / desired_file
        return None
    
    def set_service_dependency(self, service_name:str, dependency_service:str) -> bool:
        """Sets 'dependency_service' as a dependency of 'service_name' using the non-sucking-service-manager (nssm)."""
        # nssm set UT2003 DependOnService MpsSvc <= example usage 
        nssm_exe = self.find_nssm()
        command_string = f"{nssm_exe} set \"{service_name}\" \"DependOnService\" \"{dependency_service}\""
        completed_process = subprocess.call(command_string, text=True)
        match completed_process:
            case 0:
                print(f"Successfully set {dependency_service} as a dependency of {service_name}.")
                return True #success
            case 1:
                print(f"Failed to set {dependency_service} as a dependency of {service_name}.")
                return False
            case _:
                print("Failure, unhandled process exit code.")
                return False
        
    def install_lavalink_service(self) -> bool:
        """Only to be called after both 'lavalink.jar' and Java 17 have been installed on this system."""
        java_manager = JavaManager(self.operating_sys, self.machine)
        lavalink_manager = LavalinkManager(self.operating_sys, self.machine)
        java_exe = java_manager._find_java()
        lavalink_jar = lavalink_manager.find_lavalink()
        nssm_exe = self.find_nssm()
        service_name = "LavalinkService"
        command_string = command_string = f"{nssm_exe} install \"{service_name}\" \"{java_exe}\" \"{lavalink_jar}\""
        completed_process = subprocess.call(command_string, text=True)
        #NOTE I dont think the working directory needs to be changed on this service
        if completed_process == 0:
            print("-"*50 + f"\n{service_name} was installed as a service!")
            return True
        else:
            print("-"*50 +f"\n{service_name} failed to install as a service. Perhaps you have already run this script and the service already exists.\nIf you are sure the service does not already exist, try again but grant admin privileges to your shell.\nAlternatively, follow the instructions on nssm's website to manually install ParkBot as a service.")
            return False
        
    def install_bot_service(self, service_name:str = "ParkBotService") -> bool:
        """Uses the 'nssm.exe' executable to create a windows service. All the 'nssm' service does is link a python executable to a '.py' file, so that whenever the service is started, the python file is executed with the given executable."""
        self.parkbot_service = service_name
        python_venv_exe = self._find_python()
        bot_py_path = self._find_bot_py()
        nssm_exe = self.find_nssm()
        command_string = f"{nssm_exe} install \"{service_name}\" \"{python_venv_exe}\" \"{bot_py_path}\""
        completed_process = subprocess.call(command_string, text=True)
        if completed_process == 0:
            # set the services' working directory to the ParkBot working directory (one reason is for logging to work; or any other action which accesses the file system that assumes the working directory is ParkBot's root)
            change_service_directory = subprocess.call(f"{nssm_exe} set {service_name} AppDirectory {os.getcwd()}")
            if change_service_directory == 0:
                print("-"*50 + f"\n{service_name} was installed as a service!")
            else:
                print(f"{service_name} was installed but will not function until it's `working directory` is changed.\nUse the command `nssm set {service_name} AppDirectory <parkbot's-working-directory(can be found in bot.config)>")
        elif completed_process != 0:
            print("-"*50 +f"\n{service_name} failed to install as a service. Perhaps you have already run this script and the service already exists.\nIf you are sure the service does not already exist, try again but grant admin privileges to your shell.\nAlternatively, follow the instructions on nssm's website to manually install ParkBot as a service.")
            return True
        return False

class JavaManager(Downloader):
    def __init__(self, os:str, machine:str):
        super().__init__(os, machine)
        #self.machine can only be AMD64 or arm64
        match self.operating_sys:
            case "linux":
                self.java = "java"
            case "windows":
                self.java = "java.exe"
            case _:
                raise OSError(ErrorMessage.OS.value)

    def _find_java(self) -> Path | None:
        """Searches through a user's home directory given their operating system. Attempts to find an executable 'java' that exists under a parent directory which indicates it is jre 17."""
        desired_file = self.java
        user = getpass.getuser()
        match self.operating_sys:
            case "linux":
                dir_to_search = Path(f"/home/{user}")
            case "windows":
                dir_to_search = Path(f"C:/Users/{user}")
            case _:
                raise OSError(ErrorMessage.OS.value)
        
        for dirpath, dirs, files in self.walk_to_depth(dir_to_search, 5):
            for filename in files:
                if (desired_file == filename):
                    this_java = Path(dirpath) / desired_file
                    if os.access(this_java, os.X_OK) and this_java.parent.parent.name in acceptable_javas:
                        return Path(dirpath) / desired_file
        return None
    
    def get_best_link(self) -> str:
        """Returns the JRE 17 download link for the users' respective operating system."""
        if self.machine != "AMD64":
            raise OSError("The Java downloader only supports 64 bit, non-ARM architectures.")
        match self.operating_sys:
            case "windows":
                return "https://builds.openlogic.com/downloadJDK/openlogic-openjdk-jre/17.0.9+9/openlogic-openjdk-jre-17.0.9+9-windows-x64.zip"
            case "linux":
                return "https://builds.openlogic.com/downloadJDK/openlogic-openjdk-jre/17.0.9+9/openlogic-openjdk-jre-17.0.9+9-linux-x64.tar.gz"
            case _:
                raise OSError(ErrorMessage.OS.value)
    
    def download_java17(self) -> None:
        """Downloads JRE 17 to `C:/Users/<user>/Java/jdk-17` directory on Windows machines, or to the `/home/<user>/java/jdk-17/` directory on Linux machines."""
        parkbot_root = Path(os.getcwd())
        user = getpass.getuser()
        request_url = self.get_best_link()
        match self.operating_sys:
            case "windows":
                final_destination = Path(f"C:/Users/{user}/Java/jdk-17")
            case "linux":
                final_destination = Path(f"/home/{user}/java/jdk-17")
            case _:
                raise OSError(ErrorMessage.OS.value)
        self.create_directories(final_destination.parent)

        jre_name_with_ext = request_url.split("/")[-1]
        ext = jre_name_with_ext.split(".")[-1]
        match ext:
            case "gz":
                jre_name = ".".join(jre_name_with_ext.split(".")[:-2])
            case _:
                jre_name = ".".join(jre_name_with_ext.split(".")[:-1])

        download_destination = Path(parkbot_root) / jre_name_with_ext
        temp_dest = Path(parkbot_root) / "temp"

        self.create_directories(temp_dest)
        self.download_url(request_url, download_destination)
        # rename the zip directory to jdk-17.zip
        self.extract(download_destination, temp_dest) # extraction removes the .tar.gz file extension
        # extract the zip to a temporary directory, then rename the temp-directory / unzipped folder (old_name) -> extract destination / unzipped folder (new_name)
        self.move(temp_dest / jre_name, final_destination)
        temp_dest.rmdir()
        print(f"\nJava 17 installation complete. Java 17 installed to `{final_destination}`.")


class LavalinkManager(Downloader):
    #NOTE tested this class's functionality jan 21, 2024 - pass
    def __init__(self, os:str, machine:str):
        super().__init__(os, machine)
        self.configuration = {}

    @staticmethod
    def write_yaml(yaml_contents, yaml_path:Path) -> None:
        with open(yaml_path, 'w') as file:
            yaml.dump(yaml_contents, file, Dumper = yaml.Dumper)

    @staticmethod
    def read_yaml(yaml_path:Path) -> dict:
        """Reads a lavalink `application.yml` file into a Python dictionary."""
        stuff = {}
        with open(yaml_path, "r") as file:
            stuff = yaml.load(file, Loader=yaml.Loader)
        return stuff
    
    @staticmethod
    def port_is_valid(port:int) -> bool:
        port = int(port)
        if isinstance(port, int) and port > 0 and port < 65536:
            return True
        return False
    
    @staticmethod
    def string_is_valid(string:str) -> bool:
        if isinstance(string, str) and not string.isspace():
            return True
        return False
    
    @staticmethod
    def safe_get_input(condition_function, message:str):
        """Takes input until the input causes 'condition_function' to return True."""
        passing = False
        while passing is False:
            test_output = input(message)
            passing = condition_function(test_output)
        return test_output

    def find_lavalink(self) -> Path | None:
        desired_file = "lavalink.jar"
        parkbot_root = Path(os.getcwd())
        user = getpass.getuser()
        match self.operating_sys:
            case "linux":
                dirs_to_search = [parkbot_root, Path(f"/home/{user}/")]
            case "windows":
                dirs_to_search = [parkbot_root, Path(f"C:/Users/{user}")]
            case _:
                raise OSError(ErrorMessage.OS.value)
        for directory in dirs_to_search:
            for dirpath, dirs, files in self.walk_to_depth(directory, 5):
                for filename in files:
                    if (desired_file == filename):
                        return Path(dirpath) / desired_file
        return None
    
    def find_lavalink_config(self) -> Path | None:
        desired_file = "application.yml"
        desired_parent = "lavalink"
        parkbot_root = Path(os.getcwd())
        user = getpass.getuser()
        match self.operating_sys:
            case "linux":
                dirs_to_search = [parkbot_root, Path(f"/home/{user}")]
            case "windows":
                dirs_to_search = [parkbot_root, Path(f"C:/Users/{user}")]
            case _:
                raise OSError(ErrorMessage.OS.value)
        for directory in dirs_to_search:
            for dirpath, dirs, files in self.walk_to_depth(directory, 5):
                for filename in files:
                    if (desired_file == filename):
                        abs_path = Path(dirpath) / filename
                        if abs_path.parent.stem == desired_parent:
                            return abs_path
        return None
    
    def load_config(self) -> None:
        """Reads the existing 'application.yml' file into this class' configuration attribute."""
        config = self.find_lavalink_config()
        if config is None:
            raise FileNotFoundError("Failed to find 'lavalink/application.yml'.")
        self.configuration = self.read_yaml(config)
    
    def generate_lavalink_config(self, lavalink_parent_dir:Path) -> None:
        """Takes as input the directory where lavalink.jar is stored, and writes a default 'application.yml' config file in that directory."""
        lavalink_config_path = lavalink_parent_dir / "application.yml"
        if lavalink_config_path.exists():
            print(f"You already have a lavalink application.yml file. Aborting new file generation.")
            return
        response = requests.get("https://github.com/lavalink-devs/Lavalink/blob/c2431ce1b1aab088aff29033b2e44bb840fd5cd1/LavalinkServer/application.yml.example")
        response = response.content.decode("utf-8")
        lines = response.split("\n")
        with open(lavalink_config_path, "w") as file:
            for line in lines:
                file.write(line + "\n")
        
        configuration = LavalinkManager.read_yaml(lavalink_config_path)
        new_pass = LavalinkManager.safe_get_input(LavalinkManager.string_is_valid, "Enter the password you would like to assign to your Lavalink server:\n")
        lavalink_port = int(LavalinkManager.safe_get_input(LavalinkManager.port_is_valid, "Enter the port you would like Lavalink to serve on address 127.0.0.1:\n"))
        configuration['server']['address'] = "127.0.0.1"
        configuration['lavalink']['server']['password'] = new_pass
        configuration['server']['port'] = lavalink_port
        self.configuration = configuration
        LavalinkManager.write_yaml(configuration, lavalink_config_path)

    def download_lavalink(self) -> None:
        """Downloads Lavalink to the "<parkbot-root>/lavalink" directory."""
        link = "https://github.com/lavalink-devs/Lavalink/releases/download/4.0.0/Lavalink.jar"
        lavalink_dir = Path(os.getcwd()) / "lavalink"
        self.create_directories(lavalink_dir)
        self.generate_lavalink_config(lavalink_dir)
        final_dest = lavalink_dir / "lavalink.jar"
        self.download_url(link, final_dest)


class LinuxServiceManager(FileManager):

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
        """Returns the path to python executable inside ParkBot root directory, if one exists - on linux machines."""
        parkbot_root = Path(os.getcwd())
        desired_file = "python"
        for dirpath, dirs, files in os.walk(parkbot_root):
            for filename in files:
                if (filename == desired_file):
                    if os.access(Path(dirpath) / filename, os.X_OK):
                        return Path(dirpath) / desired_file
        return None    
    
    def __init__(self):
        # self.password = getpass.getpass("Please enter your linux user password:")
        self.operating_sys = platform.system().lower()
        if self.operating_sys != "linux":
            raise OSError("This manager is only compatible with Linux systems.")
        if not self.is_in_project_root():
            raise FileNotFoundError("This script was not executed in the Parkbot root directory.")

    def find_java(self) -> Path | None:
        """Searches through a user's home directory and returns the first executable instance of 'java' which exists under a parent in 'acceptable_javas'."""
        desired_file = "java"
        user = getpass.getuser()
        home_dir = Path(f"/home/{user}")
        for dirpath, dirs, files in os.walk(home_dir):
            for filename in files:
                if (desired_file == filename):
                    this_java = Path(dirpath) / desired_file
                    if os.access(this_java, os.X_OK) and this_java.parent.parent.name in acceptable_javas:
                        return Path(dirpath) / desired_file
        return None

    def find_lavalink_jar(self) -> Path | None:
        """Returns the absolute path to the first instance of 'lavalink.jar' in a user's home directory. Recurses through all sub-dirs of home."""
        desired_file = "lavalink.jar"
        parkbot_root = Path(os.getcwd())
        user = getpass.getuser()
        dirs_to_search = [parkbot_root, Path(f"/home/{user}")]
        for directory in dirs_to_search:
            for dirpath, dirs, files in os.walk(directory):
                for filename in files:
                    if (desired_file == filename):
                        return Path(dirpath) / desired_file
        return None

    def generate_parkbot_service_file(self) -> None:
        parkbot_root = Path(os.getcwd())
        parkbot_python = self.find_python()
        service_file = configparser.ConfigParser()
        service_file.optionxform = str # preserve case
        service_file["Unit"] = {
            "Description": "Discord bot service",
            "Before": "lavalink.service",
            "Requires": "lavalink.service",
        }
        service_file["Service"] = {
            "Type": "exec",
            "WorkingDirectory": f"{parkbot_root}",
            "ExecStart": f"{parkbot_python} {parkbot_root}/bot.py",
            "Restart": "on-failure",
            "RestartSec": "10",
        }
        service_file["Install"] ={
            "WantedBy": "multi-user.target",
        }

        temp_dir = parkbot_root / "parkbot.service"
        parkbot_service_path = Path("/etc/systemd/system/parkbot.service")
        with open(temp_dir, "w") as file:
            service_file.write(file)
        process = subprocess.call(["sudo", "mv", str(temp_dir), str(parkbot_service_path)])

    def generate_lavalink_service_file(self) -> None:
        parkbot_root = Path(os.getcwd())
        lavalink_jar = self.find_lavalink_jar() # both of these should 
        java = self.find_java()
        if not lavalink_jar or not java:
            raise FileNotFoundError("Failed to create lavalink.service file. Could not find either `lavalink.jar` or the java 17 executable in this user's home directory.")
        service_file = configparser.ConfigParser()
        service_file.optionxform = str # preserve case
        service_file["Unit"] = {
            "Description": "Lavalink node for serving music to Discord service",
        }
        service_file["Service"] = {
            "Type": "exec",
            "ExecStart": f"{java} -jar {lavalink_jar}",
            "Restart": "on-failure",
            "RestartSec": "10",
        }
        service_file["Install"] ={
            "WantedBy": "multi-user.target",
        }
        
        temp_dir = parkbot_root / "lavalink.service"
        lavalink_service_path = Path("/etc/systemd/system/lavalink.service")
        with open(temp_dir, "w") as file:
            service_file.write(file)
        return_code = subprocess.call(["sudo", "mv", str(temp_dir), str(lavalink_service_path)])

    def enable_parkbot_service(self) -> None:
        return_code = subprocess.call(["sudo", "systemctl", "enable", "parkbot.service"])
        match return_code:
            case 0: # success
                print("Enabled parkbot.service.")
            case 1:
                print("Failed to enable parkbot.service.")
            case _:
                print("Failed to enable parkbot.service; unhandled return code.")

    def enable_lavalink_service(self) -> None:
        return_code = subprocess.call(["sudo", "systemctl", "enable", "lavalink.service"])
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


class ExternalDependencyHandler(FileManager):
    """Class to model DependencyHandler behaviors and provide access to platform agnostic dependencies."""
    def __init__(self):
        self.operating_sys = platform.system().lower()
        self.machine = machines[platform.machine()] # can only be AMD64 or arm64

    def read(self, config_filename:str | Path) -> dict[str, dict[str, str]] | None:
        """Reads an 'ini' config file, specifically ParkBot's config file, into a Python dictionary."""
        # see if any of all config values already contain a value
        # if so, keep those existing values unless a user submits something besides a blank
        here = Path(os.getcwd())
        
        result = {}
        config = configparser.ConfigParser()
        config_path = Path(os.getcwd())  / config_filename
        success_files = config.read(config_path)
        if len(success_files) == 0:
            return None
        
        result["REQUIRED"] = dict(config.items(section="REQUIRED"))
        result["MUSIC"] = dict(config.items(section="MUSIC"))
        result["FOR-AUTOPLAY"] = dict(config.items(section="FOR-AUTOPLAY"))
        result["CANVAS"] = dict(config.items(section="CANVAS"))
        return result

    def is_in_project_root(self) -> bool:
        """Checks if the terminal is in the ParkBot root directory."""
        here = Path(os.getcwd())
        root_components = {"cogs", "data"}
        sub_dirs = set([x.name for x in here.iterdir() if x.is_dir()])
        intersection = sub_dirs.intersection(root_components)
        if root_components == intersection:
            return True
        return False

    def find_java(self) -> Path | None:
        """Returns the path to the first instance of `java.exe` which exists in this user's home directory and whose grandparent directory is 'jdk-17' or 'openlogic-openjdk-jre-17'."""
        manager = JavaManager(self.operating_sys, self.machine)
        return manager._find_java()
    
    def download_extract_jre17(self) -> Path:
        """Downloads and extracts the Java 17 to 'C:/Users/<user>/Java/jdk-17' or to 'C:/User/{user}/java/jdk-17'. Returns the path to the java executable. Assumes the script is being executed from the ParkBot root directory."""
        downloader = JavaManager(self.operating_sys, self.machine)
        java = downloader._find_java()
        if java is None:
            downloader.download_java17()
        java = downloader._find_java()
        return java
    
    def download_extract_lavalink(self) -> Path:
        """Downloads `lavalink.jar` to the ParkBot root directory if it doesn't already exist there. Returns the path to the jar."""
        #TODO need to provide a default lavalink config, 'application.yml', and perhaps allow user to set their lavalink password and port
        manager = LavalinkManager(self.operating_sys, self.machine)
        lavalink_path = manager.find_lavalink()
        if lavalink_path is None:
            manager.download_lavalink()
        lavalink_path = manager.find_lavalink()
        return lavalink_path
    
    def download_extract_all_deps(self, download_dir = None, extract_destination = None) -> dict[str, Path]:
        """Downloads and extracts all external depedencies required for the ParkBot depending on a user's OS/Machine."""
        pass
    
    def write_config(self, exe_paths:dict[str, Path]) -> None:
        """This method reads the existing 'bot.config' file if one exists, and creates a 'bot.config' file if one doesn't exist."""
        # attempt to read a config if one exists
        config_path:Path = Path(os.getcwd()) / "bot.config"

        current_config = self.read(config_path)
        new_config = configparser.ConfigParser()
        here = Path(os.getcwd())
        new_config['REQUIRED'] = {
            "TOKEN" : "",
            "WORKING_DIRECTORY" : str(here),
            "DATA_DIRECTORY" : str(Path(here) / "data"),
            "BANK_PATH" : str(Path(here) / "data" / "bank.csv"),
            "THREADS_PATH" : str(Path(here) / "data" / "threads.csv"),
            "NAUGHTY_WORDS" : "", # provide them as comma separated and parse the csv when needed
            "DB_OPTION" : "csv", # default to csv option
        }
        new_config["MYSQL"] = {
            "MYSQL_USER" : "",
            "MYSQL_PASS" : "",
            "MYSQL_URL" : "", # provide with or without PORT
            "MYSQL_DATABASE" : "",
        }
        new_config["MUSIC"] = {
            "LAVALINK_URI": str(exe_paths["lavalink_uri"]),
            "LAVALINK_PASS": str(exe_paths["lavalink_pass"]),
        }
        new_config["CANVAS"] = {
            "CANVAS_API_KEY": "",
            "CANVAS_BASE_URL": "",
            "CANVAS_COURSE_NUM": "",
            "DATETIME_FILE": str(Path(os.getcwd())  / "data" / "last_time.txt")
        }

        if current_config is not None:
            for section in new_config:
                if section in current_config:
                    for key in new_config[section]:
                        if key in current_config[section]:  # retain existing config values
                            new_config[section][key] = current_config[section][key]
        with open(config_path, "w") as configfile:
            new_config.write(configfile)
        return


class WindowsDependencyHandler(ExternalDependencyHandler):
    """Responsible for adding Windows specific dependency handling on top of the ExternalDependencyHandler."""

    def __init__(self):
        super().__init__()
        if not self.is_in_project_root():
            raise FileNotFoundError(f"Please execute this script from the ParkBot root directory.")
        username = getpass.getuser()
        self.user_home = Path("C:/Users") / username

    def download_extract_nssm(self) -> Path:
        """Downloads and extracts the NSSM archive. Returns the path to the extracted NSSM executable."""
        parkbot_root = Path(os.getcwd())
        manager = NSSMManager(self.operating_sys, self.machine)
        nssm = manager.find_nssm()
        if not nssm:
            manager.download_nssm(parkbot_root, parkbot_root)
        nssm_path = manager.find_nssm()
        return nssm_path
    
    def download_extract_all_deps(self) -> dict[str, Path]:
        results = {}
        nssm_manager = NSSMManager(self.operating_sys, self.machine)
        lavalink_manager = LavalinkManager(self.operating_sys, self.machine)
        results['nssm'] = self.download_extract_nssm()
        results['java'] = self.download_extract_jre17()
        if lavalink_manager.find_lavalink() is None:
            lavalink_manager.download_lavalink()
        else:
            lavalink_manager.load_config()
        results['lavalink'] = lavalink_manager.find_lavalink()
        results['lavalink_pass'] = lavalink_manager.configuration['lavalink']['server']['password']
        results['lavalink_uri'] = f"{lavalink_manager.configuration['server']['address']}:{lavalink_manager.configuration['server']['port']}"
        lavalink_serv_install = nssm_manager.install_lavalink_service()
        parkbot_serv_install = nssm_manager.install_bot_service()
        if parkbot_serv_install is True and lavalink_serv_install is True:
            nssm_manager.set_service_dependency(nssm_manager.parkbot_service, "LavalinkService")
        return results
    

class LinuxDependencyHandler(ExternalDependencyHandler):
    """Searches for and downloads depedencies specific to Linux."""
    def __init__(self):
        super().__init__()
        if not self.is_in_project_root():
            raise FileNotFoundError(f"Please execute this script from the ParkBot root directory.")
        username = getpass.getuser()
        self.user_home = Path("/home") / username
    
    def download_extract_all_deps(self) -> dict[str, Path]:
        """Downloads and extracts all dependencies for a Linux machine."""
        results = {}
        lavalink_manager = LavalinkManager(self.operating_sys, self.machine)
        results['java'] = self.download_extract_jre17()
        if lavalink_manager.find_lavalink() is None:
            lavalink_manager.download_lavalink()
        else:
            lavalink_manager.load_config()
        results['lavalink'] = lavalink_manager.find_lavalink()
        results['lavalink_pass'] = lavalink_manager.configuration['lavalink']['server']['password']
        results['lavalink_uri'] = f"{lavalink_manager.configuration['server']['address']}:{lavalink_manager.configuration['server']['port']}"
        service_manager = LinuxServiceManager()
        service_manager.generate_all_services()
        service_manager.enable_all_services()
        return results
    
class HandlerFactory:
    @classmethod
    def getHandler(cls):
        operating_sys:str = platform.system().lower()
        match operating_sys:
            case "windows":
                return WindowsDependencyHandler()
            case "linux":
                return LinuxDependencyHandler()
            case _:
                raise OSError(f"This program does not currently support setup for operating systems besides linux or windows.")            

if __name__ == "__main__":
    handler = HandlerFactory.getHandler()
    exe_paths = handler.download_extract_all_deps()
    handler.write_config(exe_paths)