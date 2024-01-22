import os
import shutil
import platform
import subprocess
import configparser
from enum import Enum
from pathlib import Path
from zipfile import ZipFile
from tarfile import TarFile

import bs4 
import requests

class ErrorMessage(Enum):
    OS = "The ParkBot setup script is incompatible with this operating system."
    ARCH = "The ParkBot setup script does not include full support for this architecture."


acceptable_javas = {
    "jdk-17",
    "openlogic-openjdk-jre-17",
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

class FFMPEG(Enum):
    windows = "ffmpeg.exe"
    linux = "ffmpeg"    

class JAVA(Enum):
    windows = "java.exe"
    linux = "java"

class Downloader:

    def __init__(self, os:str, machine:str):
        self.operating_sys = os
        self.machine = machine

    #thanks stackoverflow
    def downloadURL(self, url, download_destination, chunk_size=128) -> None:
        r = requests.get(url, stream=True)
        with open(download_destination, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=chunk_size):
                fd.write(chunk)

    def extractZip(self, zip_file:Path, unzip_destination:Path) -> None:
        """Extracts and deletes the specified zip archive."""
        zip = ZipFile(zip_file, "r")
        zip.extractall(unzip_destination)
        zip.close()
        os.remove(zip_file)

    def extractTar(self, tar_file:Path, extract_destination:Path) -> None:
        """Extracts and deletes the specified tar archive."""
        tar = TarFile(tar_file, "r")
        tar.extractall(extract_destination)
        tar.close()
        os.remove(tar_file)

    def extract(self, archive:Path, extract_destination:Path) -> None:
        """Extracts `archive` into `extract_destination`, and deletes `archive`."""
        match self.operating_sys:
            case "linux":
                self.extractTar(archive, extract_destination)
            case "windows":
                self.extractZip(archive, extract_destination)

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

    def _findNSSM(self, nssm_version:str) -> Path | None:
        # nssm_version accepted values : "win32" or "win64" (should probably use an enum here)
        # should really only accept win64 for now, as the rest of setup doesnt support 32
        """Searches ParkBot directory for `nssm.exe`, returns the path to the specified instance of nssm.\n\nImportant note: `nssm.exe` must exist within the ParkBot directory to successfully create a windows service using later instructions."""
        desired_file = "nssm.exe"
        parkbot_dir = Path(os.getcwd())
        for dirpath, dirs, files in os.walk(parkbot_dir):
            for filename in files:
                if (desired_file == filename) and (dirpath[-5:] == nssm_version):
                    return Path(dirpath) / desired_file
        return None
    
    def findNSSM64(self) -> Path | None:
        """Returns path to the unzipped 64-bit "nssm.exe" if it exists in ParkBot directory, user's home directory or Program Files directory."""
        return self._findNSSM("win64")
    
    def findNSSM32(self) -> Path | None:
        """Returns path to the unzipped 32-bit "nssm.exe" if it exists in ParkBot directory, user's home directory or Program Files directory."""
        return self._findNSSM("win32")

    def moveNSSM(self, nssm_location:Path, final_exe_destination:Path) -> None:
        """Pulls the nssm.exe out from its parent directory + places it in `final_exe_destination`, and deletes all unused source code/ unused exes."""
        nssm_parent_dir = Path(os.getcwd()) / "nssm-2.24"
        os.rename(nssm_location, final_exe_destination / "nssm.exe")
        shutil.rmtree(str(nssm_parent_dir))

    def downloadNSSM(self, download_dir:Path, extract_destination):
        parkbot_dir = Path(os.getcwd())
        download_url = "https://www.nssm.cc/release/nssm-2.24.zip"
        nssm_destination = download_dir / "nssm.zip"
        self.downloadURL(download_url, nssm_destination)
        self.extractZip(nssm_destination, extract_destination)
        nssm_path = self.findNSSM64()
        if nssm_path is not None:
            self.moveNSSM(nssm_path, parkbot_dir)
        else:
            raise IOError(f"Attempted to download `nssm.exe`, but cannot find it in file system.")

    def _findPython(self) -> Path | None:
        """Searches ParkBot's directory for a virtual environment and returns the path to its python executable."""
        desired_file = "python.exe"
        parkbot_dir = Path(os.getcwd())
        for dirpath, dirs, files in os.walk(parkbot_dir):
            for dir in dirs:
                for dirpath, dirs, files in os.walk(dir):
                    for filename in files:
                        if (desired_file == filename):
                            return Path(dirpath).absolute() / desired_file
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

    def installBotService(self, service_name:str = "ParkBotService") -> bool:
        """Uses the 'nssm.exe' executable to create a windows service. All the 'nssm' service does is link a python executable to a '.py' file, so that whenever the service is started, the python file is executed with the given executable."""
        python_venv_exe = self._findPython()
        bot_py_path = self._findBotPy()
        command_string = f"nssm install \"{service_name}\" \"{python_venv_exe}\" \"{bot_py_path}\""
        completed_process = subprocess.call(command_string, text=True)
        if completed_process == 0:
            # set the services' working directory to the ParkBot working directory (one reason is for logging to work; or any other action which accesses the file system that assumes the working directory is ParkBot's root)
            change_service_directory = subprocess.call(f"nssm set {service_name} AppDirectory {os.getcwd()}")
            if change_service_directory == 0:
                print("-"*50 + f"\n{service_name} was installed as a service!")
            else:
                print(f"{service_name} was installed but will not function until it's `working directory` is changed.\nUse the command `nssm set {service_name} AppDirectory <parkbot's-working-directory(can be found in bot.config)>")
        elif completed_process != 0:
            print("-"*50 +f"\n{service_name} failed to install as a service. Try again but grant admin privileges when prompted.\nAlternatively, follow the instructions on nssm's website to manually install ParkBot as a service.")
            return True
        return False
    
    def installLavalinkService(self) -> bool:
        java_manager = JavaManager(self.operating_sys, self.machine)
        lavalink_manager = LavalinkManager(self.operating_sys, self.machine)
        java_exe = java_manager._findJava()
        lavalink_jar = lavalink_manager.findLavalink()
        service_name = "LavalinkService"
        command_string = command_string = f"nssm install \"{service_name}\" \"{java_exe}\" \"{lavalink_jar}\""
        completed_process = subprocess.call(command_string, text=True)
        #NOTE I dont think the working directory needs to be changed on this service
        if completed_process == 0:
            print("-"*50 + f"\n{service_name} was installed as a service!")
            return True
        else:
            print("-"*50 +f"\n{service_name} failed to install as a service. Try again but grant admin privileges when prompted.\nAlternatively, follow the instructions on nssm's website to manually install ParkBot as a service.")
            return False

    
class FFMPEGManager(Downloader):
    """Downloads + extracts FFMPEG archive based on user OS and CPU architecture."""

    def __init__(self, os:str, machine:str):
        super().__init__(os, machine)
        #self.operating_sys
        #self.machine
        self.builds = self.getBuilds()
        match self.operating_sys:
            case "windows":
                self.ffmpeg = 'ffmpeg.exe'
            case "linux":
                self.ffmpeg = 'ffmpeg'
            case _:
                raise OSError(ErrorMessage.OS.value)

        # {
        # linux64-gpl-shared-tar
        # linux64-gpl-tar
        # linux64-lgpl-shared-tar
        # linux64-lgpl-tar
        # linuxarm64-gpl-shared-tar
        # linuxarm64-gpl-tar
        # linuxarm64-lgpl-shared-tar
        # linuxarm64-lgpl-tar
        # win64-gpl-shared-zip
        # win64-gpl-zip 
        # }

        self.best_match = None

    def _findFFMPEG(self) -> Path | None:
        # nssm_version accepted values : "win32" or "win64" (should probably use an enum here)
        # should really only accept win64 for now, as the rest of setup doesnt support 32
        """Searches ParkBot directory for `ffmpeg.exe`, returns the path to it."""
        desired_file = self.ffmpeg
        parkbot_dir = Path(os.getcwd())
        for dirpath, dirs, files in os.walk(parkbot_dir):
            for filename in files:
                if (desired_file == filename):
                    return Path(dirpath) / desired_file
        return None

    # linux64-gpl-shared-tar, https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl-shared.tar.xz
    # linux64-gpl-tar, https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz
    # linux64-lgpl-shared-tar, https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-lgpl-shared.tar.xz
    def getBuilds(self) -> dict[str, str]:
        host = "https://github.com"
        """GET requests a github repo that hosts FFMPEG builds, and parses response's contents to return a dictionary of {'build_name':'build_download_link'}"""
        response = requests.get("https://github.com/BtbN/FFmpeg-Builds/releases")
        soup = bs4.BeautifulSoup(response.content, "html.parser")
        list_items = soup.find_all("li", attrs={"class":"Box-row d-flex flex-column flex-md-row"})
        results = {}
        for item in list_items:
            title = item.find("span", attrs={"class":"Truncate-text text-bold"})
            if (title is not None) and (title.text != "Source code") and (title.text != ""):
                # print(title.text)
                words = title.text.split("-")
                words = words[:-1] + words[-1].split(".")[:2]
                tit = ("-".join(words[3:]))
                link = item.find("a", attrs={"class":"Truncate"})
                link = link["href"]
                results[tit] = host + link
        return results
    
    def getBestLinuxBuildLink(self, builds) -> str:
        "Gets download link for Linux depending on user's CPU instruction set."
        match self.machine:
            case "AMD64":
                return builds["linux64-lgpl-tar"]
            case "arm64":
                return builds["linuxarm64-lgpl-tar"]
            case _:
                raise OSError(ErrorMessage.ARCH.value)

    def getDownloadLink(self, builds):
        """Returns the appropriate FFMPEG download link for a user's operating system."""
        match self.operating_sys:
            case "windows":
                return builds["win64-gpl-zip"]
            case "linux":
                return self.getBestLinuxBuildLink(builds)
            case _:
                raise OSError(ErrorMessage.OS.value)
    
    def moveFFMPEG(self, ffmpeg_location:Path, ffmpeg_parent_dir:Path, final_exe_destination:Path) -> None:
        """Pulls the ffmpeg.exe out from its parent directory + places it in `final_exe_destination`, and deletes all unused source code/ unused exes."""
        os.rename(ffmpeg_location, final_exe_destination / self.ffmpeg)
        shutil.rmtree(str(ffmpeg_parent_dir))

    def _downloadFFMPEG(self, download_dir:Path, extract_destination) -> None:
        """Downloads FFMPEG archive, extracts the archive to `extract_destination` and deletes the archive."""
        parkbot_dir = Path(os.getcwd())
        match self.operating_sys:
            case "windows":
                file_ext = ".zip"
            case "linux":
                file_ext = ".tar.xz"
            case _:
                raise OSError(ErrorMessage.OS.value)
        download_destination = download_dir / f"ffmpeg{file_ext}"
        link = self.getDownloadLink(self.builds)
        self.downloadURL(link, download_destination)
        self.extract(download_destination, extract_destination)
        ffmpeg_exe_location = self._findFFMPEG()
        ffmpeg_parent_directory = ffmpeg_exe_location.parent.parent 
        self.moveFFMPEG(ffmpeg_exe_location, ffmpeg_parent_directory, parkbot_dir)


class JavaManager(Downloader):
    def __init__(self, os:str, machine:str):
        super().__init__(os, machine)
        #self.machine can only be AMD64 or arm64
        match self.operating_sys:
            case "linux":
                self.java = "java"
            case "windows":
                self.java = "java.exe"

    def _findJava(self) -> Path | None:
        """Searches through a user's home directory given their operating system. On windows, also attempts to find an executable "java.exe" that exists under a parent directory which indicates it is jre 17."""
        desired_file = self.java
        user = os.getlogin()
        print("You may be met with a prompt to elevate to admin privileges. This bump in privileges is necessary to search your 'Program Files' directory for an existing java executable.")
        match self.operating_sys:
            case "linux":
                #NOTE just search user's home since we're assuming user doesn't have admin privileges
                dirs_to_search = [Path("~/")]
            case "windows":
                dirs_to_search = [Path("C://Program Files/"), Path(f"C://Users/{user}")]
            case _:
                raise OSError(ErrorMessage.OS.value)
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
    
    def getBestLink(self) -> str:
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
    
    def downloadJava17(self) -> None:
        """Downloads JRE 17 to `C://Users/<user>/Java/jdk-17` directory on Windows machines, or to the `/home/<user>/java/jdk-17/` directory on Linux machines."""
        download_dir = Path(os.getcwd())
        user = os.getlogin()
        request_url = self.getBestLink()
        match self.operating_sys:
            case "windows":
                final_destination = Path(f"C://Users/{user}/Java/jdk-17")
            case "linux":
                final_destination = Path("~/java/jdk-17")
            case _:
                raise OSError(ErrorMessage.OS.value)
        self.create_directories(final_destination.parent)
        
        jre_name_with_ext = request_url.split("/")[-1]
        jre_name = ".".join(jre_name_with_ext.split(".")[:-1])
        download_destination = Path(download_dir) / jre_name_with_ext
        temp_dest = Path(download_dir) / "temp"

        self.create_directories(temp_dest)
        self.downloadURL(request_url, download_destination)
        # rename the zip directory to jdk-17.zip
        self.extract(download_destination, temp_dest)
        # extract the zip to a temporary directory, then rename the temp-directory / unzipped folder (old_name) -> extract destination / unzipped folder (new_name)
        self.move(temp_dest / jre_name, final_destination)
        temp_dest.rmdir()
        print(f"Java 17 installation complete. Java 17 installed to `{final_destination}`.")


class LavalinkManager(Downloader):
    def __init__(self, os:str, machine:str):
        super().__init__(os, machine)

    def findLavalink(self) -> Path | None:
        desired_file = "lavalink.jar"
        user = os.getlogin()
        match self.operating_sys:
            case "linux":
                dirs_to_search = [Path("~/")]
            case "windows":
                dirs_to_search = [Path(f"C://Users/{user}")]
            case _:
                raise OSError(ErrorMessage.OS.value)
        for directory in dirs_to_search:
            for dirpath, dirs, files in os.walk(directory):
                for filename in files:
                    if (desired_file == filename):
                        return Path(dirpath) / desired_file
        return None

    def downloadLavalink(self) -> None:
        """Downloads Lavalink to the Parkbot project's root directory. Returns the path to 'lavalink.jar'."""
        link = "https://github.com/lavalink-devs/Lavalink/releases/download/4.0.0/Lavalink.jar"
        download_dest = Path(os.getcwd())
        self.downloadURL(link, download_dest)


#TODO finish implementing the WindowsDepednecyHandler and LinuxDependencyHandler abilities to download/install openjdk-17 and lavalink - then configure lavalink and create a service for it (in the case of windows)

class ExternalDependencyHandler:
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

    def isInProjectRoot(self) -> bool:
        """Checks if the terminal is in the ParkBot root directory."""
        here = Path(os.getcwd())
        root_components = {"cogs", "data"}
        sub_dirs = set([x.name for x in here.iterdir() if x.is_dir()])
        intersection = sub_dirs.intersection(root_components)
        if root_components == intersection:
            return True
        return False
    
    def findFile(self, desired_file:str, where_to_look:list[Path]) -> Path | None:
        """Searches specified directories for a desired file, returns the path to the first instance of the desired file."""
        for dir in where_to_look:
            for root, dir, files in os.walk(dir):
                if desired_file in files:
                    return Path(root) / desired_file
        return None

    def findFFMPEG(self) -> Path | None:
        """Returns a Path to the first found instance of the ffmpeg executable."""
        manager = FFMPEGManager(self.operating_sys, self.machine)
        return manager._findFFMPEG()

    def findJava(self) -> Path | None:
        """Returns the path to the first instance of `java.exe` which exists in this user's home directory and whose grandparent directory is 'jdk-17' or 'openlogic-openjdk-jre-17'."""
        manager = JavaManager(self.operating_sys, self.machine)
        return manager._findJava()

    def downloadExtractFFMPEG(self, download_dir = None, extract_destination = None) -> Path:
        """Downloads and extracts the FFMPEG archive. Returns the path to the extracted FFMPEG executable."""
        ffmpeg = self.findFFMPEG()
        here = Path(os.getcwd())
        if not ffmpeg:
            if download_dir is None:
                download_dir = here
            if extract_destination is None:
                extract_destination = here
            downloader = FFMPEGManager(self.operating_sys, self.machine)
            downloader._downloadFFMPEG(download_dir, extract_destination)
        ffmpeg = self.findFFMPEG()
        return ffmpeg
    
    def downloadExtractJRE17(self) -> Path:
        """Downloads and extracts the Java 17 to 'C://Users/<user>/Java/jdk-17' or to 'C://User/{user}/java/jdk-17'. Returns the path to the java executable. Assumes the script is being executed from the ParkBot root directory."""
        downloader = JavaManager(self.operating_sys, self.machine)
        java = downloader._findJava()
        if java is None:
            downloader.downloadJava17()
        java = downloader._findJava()
        return java
    
    def downloadExtractLavalink(self) -> Path:
        """Downloads `lavalink.jar` to the ParkBot root directory if it doesn't already exist there. Returns the path to the jar."""
        manager = LavalinkManager(self.operating_sys, self.machine)
        lavalink_path = manager.findLavalink()
        if lavalink_path is None:
            manager.downloadLavalink()
        lavalink_path = manager.findLavalink()
        return lavalink_path
    
    def downloadExtractAllDeps(self, download_dir = None, extract_destination = None) -> dict[str, Path]:
        """Downloads and extracts all external depedencies required for the ParkBot depending on a user's OS/Machine."""
        pass
    
    def writeConfig(self, exe_paths:dict[str, Path]) -> None:
        """This method reads the existing 'bot.config' file if one exists, and creates a 'bot.config' file if one doesn't exist."""
        # attempt to read a config if one exists
        ffmpeg_path = exe_paths["ffmpeg"]
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
        }
        new_config["MUSIC"] = {
            "FFMPEG_PATH" : str(ffmpeg_path),
            "GOOGLE_API_KEY" : "",
            "LAVALINK_URI": "127.0.0.1:2333",
            "LAVALINK_PASS": "",
        }
        new_config["FOR-AUTOPLAY"] = {
            "SPOTIFY_CLIENT_ID" : "",
            "SPOTIFY_CLIENT_SECRET" : "",
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
                        if key in current_config[section]:
                            new_config[section][key] = current_config[section][key]
                            # retain values that already exist, rather than overwriting them

        with open(config_path, "w") as configfile:
            new_config.write(configfile)
        return


class WindowsDependencyHandler(ExternalDependencyHandler):
    """Responsible for adding Windows specific dependency handling on top of the ExternalDependencyHandler."""

    def __init__(self):
        super().__init__()
        if not self.isInProjectRoot():
            raise FileNotFoundError(f"Please execute this script from the ParkBot root directory.")
        username = os.getlogin()
        self.user_home = Path("C:/Users") / username
    
    def findNSSM(self) -> Path | None:
        """Returns path to "nssm.exe" if it exists in ParkBot directory, user's home directory or Program Files directory."""
        parkbot = Path(os.getcwd())
        # dirs_to_search = [parkbot, self.user_home, Path("C:/Program Files")]
        dirs_to_search = [parkbot]
        return self.findFile("nssm.exe", dirs_to_search)

    def downloadExtractNSSM(self, download_dir = None, extract_destination = None) -> Path:
        """Downloads and extracts the FFMPEG archive. Returns the path to the extracted FFMPEG executable."""
        nssm = self.findNSSM()
        here = Path(os.getcwd())
        if not nssm:
            if download_dir is None:
                download_dir = here
            if extract_destination is None:
                extract_destination = here
            downloader = NSSMManager(self.operating_sys, self.machine)
            downloader.downloadNSSM(download_dir, extract_destination)
        nssm_path = self.findNSSM()
        return nssm_path
    
    def downloadExtractAllDeps(self, download_dir=None, extract_destination=None) -> dict[str, Path]:
        nssm_manager = NSSMManager(self.operating_sys, self.machine)
        results = {}
        results['ffmpeg'] = self.downloadExtractFFMPEG(download_dir, extract_destination)
        results['nssm'] = self.downloadExtractNSSM(download_dir, extract_destination)
        results['java'] = self.downloadExtractJRE17()
        results['lavalink'] = self.downloadExtractLavalink()
        nssm_manager.installLavalinkService()
        nssm_manager.installBotService()
        return results
    
    #TODO create lavalink service and cite it as a dependency for ParkBotService

class LinuxDependencyHandler(ExternalDependencyHandler):
    """Searches for and downloads depedencies specific to Linux."""
    def __init__(self):
        super().__init__()
        if not self.isInProjectRoot():
            raise FileNotFoundError(f"Please execute this script from the ParkBot root directory.")
        username = os.getlogin()
        self.user_home = Path("/home") / username

    def findFFMPEG(self) -> Path | None:
        """Checks a user's home directory, opt, and usr/local directories for ffmpeg.exe. Returns path of the first instance it finds."""
        parkbot = Path(os.getcwd())
        usr_local = Path("/usr/local/")
        opt = Path("/opt/")
        dirs_to_search = [parkbot, self.user_home, usr_local, opt]
        return self.findFile(FFMPEG.linux.value, dirs_to_search)
    
    def downloadExtractAllDeps(self, download_dir=None, extract_destination=None) -> dict[str, Path]:
        results = {}
        results['ffmpeg'] = self.downloadExtractFFMPEG(download_dir, extract_destination)
        results['java'] = self.downloadExtractJRE17()
        results['lavalink'] = self.downloadExtractLavalink()
        #TODO use systemd to create lavalink service
        #TODO use systemd to create ParkBotService, with lavalink service as a dependency
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
    exe_paths = handler.downloadExtractAllDeps()
    handler.writeConfig(exe_paths)