import requests
import bs4 
import os
import platform
from pathlib import Path
from enum import Enum
from zipfile import ZipFile
from tarfile import TarFile
import configparser
import shutil
import subprocess
import time

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

class OSHome(Enum):
    windows = Path("C:/Users/")
    linux = Path("/home/")

class FFMPEG(Enum):
    windows = "ffmpeg.exe"
    linux = "ffmpeg"    


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

    def extractZip(self, zip_file, unzip_destination) -> None:
        """Extracts and deletes the specified zip archive."""
        zip = ZipFile(zip_file, "r")
        zip.extractall(unzip_destination)
        zip.close()
        os.remove(zip_file)

    def extractTar(self, tar_file, extract_destination) -> None:
        """Extracts and deletes the specified tar archive."""
        tar = TarFile(tar_file, "r")
        tar.extractall(extract_destination)
        tar.close()
        os.remove(tar_file)

    def extract(self, archive, extract_destination) -> None:
        """Extracts `archive` into `extract_destination`, and deletes `archive`."""
        match self.operating_sys:
            case "linux":
                self.extractTar(archive, extract_destination)
            case "windows":
                self.extractZip(archive, extract_destination)

class NSSMConfigurator:

    # def _findNSSM(self) -> Path | None:
    # # nssm_version accepted values : "win32" or "win64" (should probably use an enum here)
    # # should really only accept win64 for now, as the rest of setup doesnt support 32
    #     """Searches ParkBot directory for `nssm.exe`, returns the path to the specified instance of nssm.\n\nImportant note: `nssm.exe` must exist within the ParkBot directory to successfully create a windows service using later instructions."""
    #     desired_file = "nssm.exe"
    #     parkbot_dir = Path(os.getcwd())
    #     for dirpath, dirs, files in os.walk(parkbot_dir):
    #         for filename in files:
    #             if (desired_file == filename):
    #                 return Path(dirpath) / desired_file
    #     return None
    
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
            # set the services' working directory to the ParkBot working directory
            change_service_directory = subprocess.call(f"nssm set {service_name} AppDirectory {os.getcwd()}")
            if change_service_directory == 0:
                print("-"*50 + f"\n{service_name} was installed as a service!")
            else:
                print(f"{service_name} was installed but will not function until it's `working directory` is changed.\nUse the command `nssm set {service_name} AppDirectory <parkbot's-working-directory(can be found in bot.config)>")
        elif completed_process != 0:
            print("-"*50 +f"\n{service_name} failed to install as a service. Try again but grant admin privileges when prompted.\nAlternatively, follow the instructions on nssm's website to manually install ParkBot as a service.")
            return True
        return False


class NSSMDownloader(Downloader):

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
    
    # https://www.devdungeon.com/content/run-python-script-windows-service - instructions for using nssm after installation
    """Downloads the most recent stable version of NSSM.exe (the non-sucking-service-manager)."""
    def __init__(self, os:str, machine:str):
        super().__init__(os, machine)
        if self.operating_sys != 'windows':
            raise OSError(f"No need to download NSSM on an operating system besides windows.")

    def findNSSM64(self) -> Path | None:
        """Returns path to 64 bit "nssm.exe" if it exists in ParkBot directory, user's home directory or Program Files directory."""
        return self._findNSSM("win64")
    
    def findNSSM32(self) -> Path | None:
        """Returns path to 32 bit "nssm.exe" if it exists in ParkBot directory, user's home directory or Program Files directory."""
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

class FFMPEGDownloader(Downloader):
    """Downloads + extracts FFMPEG archive based on user OS and CPU architecture."""

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

    def getBestLinuxBuildLink(self, builds) -> str:
        "Gets download link for Linux depending on user's CPU instruction set."
        match self.machine:
            case "AMD64":
                return builds["linux64-lgpl-tar"]
            case "arm64":
                return builds["linuxarm64-lgpl-tar"]
            case _:
                raise OSError(f"This computer's architecture is not currently supported for easy setup.")

    def getDownloadLink(self, builds):
        """Returns the appropriate FFMPEG download link for a user's operating system."""
        match self.operating_sys:
            case "windows":
                return builds["win64-gpl-zip"]
            case "linux":
                return self.getBestLinuxBuildLink(builds)
            case _:
                raise OSError("This computer's architecture is not currently supported for easy setup.")
    
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
                raise OSError()
        download_destination = download_dir / f"ffmpeg{file_ext}"
        link = self.getDownloadLink(self.builds)
        self.downloadURL(link, download_destination)
        self.extract(download_destination, extract_destination)
        ffmpeg_exe_location = self._findFFMPEG()
        ffmpeg_parent_directory = ffmpeg_exe_location.parent.parent 
        self.moveFFMPEG(ffmpeg_exe_location, ffmpeg_parent_directory, parkbot_dir)


class ExternalDependencyHandler:
    """Super class to model DependencyHandler behaviors and provide basic operations."""
    def __init__(self):
        self.operating_sys = platform.system().lower()
        self.machine = machines[platform.machine()]

    def read(self, config_filename:str | Path) -> dict[str, dict[str, str]] | None:
        """Reads an 'ini' config file, specifically ParkBot's config file, into a Python dictionary."""
        # see if any of all config values already contain a value
        # if so, keep those existing values unless a user submits something besides a blank
        here = Path(os.getcwd())
        
        result = {}
        config = configparser.ConfigParser()
        config_path = Path(os.getcwd())  / config_filename
        file = config.read(config_path)
        if file is None:
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
        pass

    def downloadExtractFFMPEG(self, download_dir = None, extract_destination = None) -> Path:
        """Downloads and extracts the FFMPEG archive. Returns the path to the extracted FFMPEG executable."""
        ffmpeg = self.findFFMPEG()
        here = Path(os.getcwd())
        if not ffmpeg:
            if download_dir is None:
                download_dir = here
            if extract_destination is None:
                extract_destination = here
            downloader = FFMPEGDownloader(self.operating_sys, self.machine)
            downloader._downloadFFMPEG(download_dir, extract_destination)
        ffmpeg = self.findFFMPEG()
        return ffmpeg
    
    def downloadExtractAllDeps(self, download_dir = None, extract_destination = None) -> dict[str, Path]:
        """Downloads and extracts all external depedencies required for the ParkBot depending on a user's OS/Machine."""
        pass
    
    def writeConfig(self, exe_paths:dict[str, Path]) -> None:
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
    """Searches for and downloads depedencies specific to Windows."""

    def __init__(self):
        super().__init__()
        if not self.isInProjectRoot():
            raise FileNotFoundError(f"Please execute this script from the ParkBot root directory.")
        username = os.getlogin()
        self.user_home = Path("C:/Users") / username

    def findFFMPEG(self) -> Path | None:
        """Returns the path to 'ffmpeg.exe' if it exists in ParkBot directory, `C:\\Users\\<user>\\`, or `C:\\Program Files\\`"""
        parkbot = Path(os.getcwd())
        # dirs_to_search = [parkbot, self.user_home, Path("C:/Program Files")]
        dirs_to_search = [parkbot]
        return self.findFile(FFMPEG.windows.value, dirs_to_search)
    
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
            downloader = NSSMDownloader(self.operating_sys, self.machine)
            downloader.downloadNSSM(download_dir, extract_destination)
        nssm_path = self.findNSSM()
        return nssm_path
    
    def downloadExtractAllDeps(self, download_dir=None, extract_destination=None) -> dict[str, Path]:
        configurator = NSSMConfigurator()
        results = {}
        results['ffmpeg'] = self.downloadExtractFFMPEG(download_dir, extract_destination)
        results['nssm'] = self.downloadExtractNSSM(download_dir, extract_destination)
        configurator.installBotService()
        return results
    


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