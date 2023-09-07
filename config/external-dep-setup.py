import requests
import bs4 
import os
import platform
from pathlib import Path
from enum import Enum

platforms = {
    "linux": "linux",
    "windows": "windows",
    # "darwin": "mac",
}

class OSHome(Enum):
    windows = Path("C:/Users/")
    linux = Path("/home/")

class FFMPEG(Enum):
    windows = "ffmpeg.exe"
    linux = "ffmpeg"

class HandlerFactory:
    @classmethod
    def getHandler(cls):
        try:
            operating_sys:str = platforms[platform.system().lower()]
            match operating_sys:
                case "windows":
                    return WindowsDependencyHandler(operating_sys)
                case "linux":
                    return LinuxDependencyHandler(operating_sys)
        except KeyError:
            raise OSError(f"This program does not currently support setup for operating systems besides linux or windows.")
            

class ExternalDependencyHandler:
    """Abstract class to model DependencyHandler behaviors"""

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

    


class WindowsDependencyHandler(ExternalDependencyHandler):
    """Searches for and downloads depedencies specific to Windows."""

    def __init__(self, operating_sys):
        if not self.isInProjectRoot():
            raise FileNotFoundError(f"Please execute this script from the ParkBot root directory.")
        if operating_sys != "windows":
            raise OSError(f"Setup Handler spawned the wrong version of it's depedency handler. Please try to run the setup.sh script again.")
        self.operating_sys = operating_sys

    def findFFMPEG(self) -> Path | None:
        """Returns the path to 'ffmpeg.exe' if it exists in `C:\\Users\\<user>\\` or `C:\\Program Files\\`"""
        username = os.getlogin()
        user_home_dir = Path("C:/Users") / username
        parkbot = Path(os.getcwd())
        dirs_to_search = [parkbot, user_home_dir, Path("C:/Program Files")]

        return self.findFile(FFMPEG.windows.value, dirs_to_search)
    
    def findNSSM(self) -> Path | None:
        pass
    
    

class LinuxDependencyHandler(ExternalDependencyHandler):
    """Searches for and downloads depedencies specific to Linux."""
    def __init__(self, operating_sys):
        if not self.isInProjectRoot():
            raise FileNotFoundError(f"Please execute this script from the ParkBot root directory.")
        if operating_sys != "linux":
            raise OSError(f"Setup Handler spawned the wrong version of it's depedency handler. Please try to run the setup.sh script again.")
        
    def getFFMPEGPathLinux(self) -> Path | None:
        """Checks a user's home directory, opt, and usr/local directories for ffmpeg.exe. Returns path of the first instance it finds."""
        parkbot = Path(os.getcwd())
        username = os.getlogin()
        user_home = Path("/home") / username
        usr_local = Path("/usr/local/")
        opt = Path("/opt/")
    
        dirs_to_search = [parkbot, user_home, usr_local, opt]
        return self.findFile(FFMPEG.linux.value, dirs_to_search)

class FFMPEGDownloader:
    """Parses different versions of FFMPEG."""
    
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
    
    def getBestBuild(self, operating_system)
    def __init__(self, os:str):
        self.operating_sys = os
        self.builds = self.getBuilds()
        # download proper version then download NSSM
        self.best_match = ""


    def getDownloadLink(self, platform:str) -> str:
        """Returns the most appropriate FFMPEG download link for a user's operating system."""
        
class WindowsDownloader(FFMPEGDownloader):
    def __init__(self, )


if __name__ == "__main__":
    handler = HandlerFactory.getHandler()



