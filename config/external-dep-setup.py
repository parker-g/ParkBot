import requests
import bs4 
import os
import platform
from pathlib import Path
from enum import Enum
from zipfile import ZipFile
from tarfile import TarFile
import configparser

systems = {
    "linux": "linux",
    "windows": "windows",
    # "darwin": "mac",
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

class OSHome(Enum):
    windows = Path("C:/Users/")
    linux = Path("/home/")

class FFMPEG(Enum):
    windows = "ffmpeg.exe"
    linux = "ffmpeg"

class FFMPEGDownloader:
    """Downloads + extracts FFMPEG archive based on user OS and CPU architecture."""
    
    #thanks stackoverflow
    def downloadURL(self, url, save_path, chunk_size=128) -> None:
        r = requests.get(url, stream=True)
        with open(save_path, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=chunk_size):
                fd.write(chunk)

    def extract(self, archive, extract_destination) -> None:
        """Extracts `archive` into `extract_destination`."""
        match self.operating_sys:
            case "linux":
                self.extractTar(archive, extract_destination)
            case "windows":
                self.extractZip(archive, extract_destination)
        
    def extractZip(self, zip_file, unzip_destination) -> None:
        zip = ZipFile(zip_file, "r")
        zip.extractall(unzip_destination)

    def extractTar(self, tar_file, extract_destination) -> None:
        tar = TarFile(tar_file, "r")
        tar.extractall(extract_destination)

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
                print(title.text)
                words = title.text.split("-")
                words = words[:-1] + words[-1].split(".")[:2]
                tit = ("-".join(words[3:]))
                link = item.find("a", attrs={"class":"Truncate"})
                link = link["href"]
                results[tit] = host + link
        return results
    
    def __init__(self, os:str, machine:str, download_destination = None):
        self.operating_sys = os
        self.machine = machine
        self.builds = self.getBuilds()
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
        self.download_destination = download_destination

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
        """Returns the most appropriate FFMPEG download link for a user's operating system."""
        match self.operating_sys:
            case "windows":
                return builds["win64-gpl-zip"]
            case "linux":
                return self.getBestLinuxBuildLink(builds)
            case _:
                raise OSError("This computer's architecture is not currently supported for easy setup.")
            

    def downloadFFMPEG(self, download_destination, extract_destination) -> None:
        link = self.getDownloadLink(self.builds)
        self.downloadURL(link, download_destination) # downloads zip
        self.extract(download_destination, extract_destination)
        

class ExternalDependencyHandler:
    """Super class to model DependencyHandler behaviors and provide basic operations."""
    def __init__(self):
        self.operating_sys = platform.system().lower()
        self.machine = machines[platform.machine()]

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

    def findFFMPEG(self, operating_system:str) -> Path | None:
        pass

    def main(self, download_dest, extract_destination):
        ffmpeg = self.findFFMPEG(self.operating_sys)
        parkbot_scripts_dir = Path(os.getcwd()) / ".venv" / "Scripts"
        if not ffmpeg:
            downloader = FFMPEGDownloader(self.operating_sys, self.machine)
            downloader.downloadFFMPEG(parkbot_scripts_dir)

class WindowsDependencyHandler(ExternalDependencyHandler):
    """Searches for and downloads depedencies specific to Windows."""

    def __init__(self):
        super().__init__()
        if not self.isInProjectRoot():
            raise FileNotFoundError(f"Please execute this script from the ParkBot root directory.")
        username = os.getlogin()
        self.user_home = Path("C:/Users") / username


    def findFFMPEG(self) -> Path | None:
        """Returns the path to 'ffmpeg.exe' if it exists in `C:\\Users\\<user>\\` or `C:\\Program Files\\`"""
        parkbot = Path(os.getcwd())
        dirs_to_search = [parkbot, self.user_home, Path("C:/Program Files")]

        return self.findFile(FFMPEG.windows.value, dirs_to_search)
    
    def findNSSM(self) -> Path | None:
        """Returns path to "nssm.exe" if it exists in ParkBot direectory, user's home directory or Program Files directory."""
        parkbot = Path(os.getcwd())
        dirs_to_search = [parkbot, self.user_home, Path("C:/Program Files")]

        return self.findFile("nssm.exe", dirs_to_search)
    
    

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

class HandlerFactory:
    @classmethod
    def getHandler(cls):
        try:
            operating_sys:str = platform.system().lower()
            match operating_sys:
                case "windows":
                    return WindowsDependencyHandler()
                case "linux":
                    return LinuxDependencyHandler()
        except KeyError:
            raise OSError(f"This program does not currently support setup for operating systems besides linux or windows.")


if __name__ == "__main__":
    handler = HandlerFactory.getHandler()




