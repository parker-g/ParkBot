import requests
import bs4 
import os
import platform
from pathlib import Path
from enum import Enum

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

class OSHome(Enum):
    windows = Path("C:/Users/")
    linux = Path("/home/")

class FFMPEG(Enum):
    windows = "ffmpeg.exe"
    linux = "ffmpeg"

class FFMPEGDownloader:
    """Parses different versions of FFMPEG."""
    
    #NOTE this host only has linux 64 bit, linux ARM 64 bit, and win64 bit builds
    #NOTE prioritize LGPL builds (GPL builds require works that use them to also be licensed under GPL)
    
    #NOTE perhaps check the user's architecture BEFORE grabbing the builds page. that way I can look for the user's proper build 
    # based on their arc

    def getBuilds(self) -> dict[str, str]:
        """GET requests a github repo that hosts FFMPEG builds, and parses response's contents to return a dictionary of {'build_name':'build_download_link'}"""
        response = requests.get("https://github.com/BtbN/FFmpeg-Builds/releases")
        soup = bs4.BeautifulSoup(response.content, "html.parser")
        list_items = soup.find_all("li", attrs={"class":"Box-row d-flex flex-column flex-md-row"})
        results = {}
        for item in list_items:
            title = item.find("span", attrs={"class":"Truncate-text text-bold"})
            if title is not None:
                tit = title.text
            link = item.find("a", attrs={"class":"Truncate"})
            if link is not None:
                final_link = link["href"]
            results[tit] = final_link
        return results
    
    def getBestBuild(self, operating_system):
    
    def downloadFFMPEG(self, destination:Path) -> None:
        pass

    def __init__(self, os:str):
        self.operating_sys = os
        self.builds = self.getBuilds()
        # download proper version then download NSSM
        self.best_match = ""


    def getDownloadLink(self, platform:str) -> str:
        """Returns the most appropriate FFMPEG download link for a user's operating system."""

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


class ExternalDependencyHandler:
    """Abstract class to model DependencyHandler behaviors"""
    def __init__(self):
        self.operating_sys = platform.system().lower()

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

    def main(self):
        ffmpeg = self.findFFMPEG(self.operating_sys)
        parkbot_scripts_dir = Path(os.getcwd()) / ".venv" / "Scripts"
        if not ffmpeg:
            client = FFMPEGDownloader()
            client.downloadFFMPEG(parkbot_scripts_dir) # download FFMPEG to the parkbot direectory

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


        
class WindowsDownloader(FFMPEGDownloader):
    def __init__(self, )


if __name__ == "__main__":
    handler = HandlerFactory.getHandler()




