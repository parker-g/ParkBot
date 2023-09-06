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
    """Abstract class to Handle downloading ParkBot dependencies that can't be installed through pip."""

    def isInProjectRoot(self) -> bool:
        """Checks if the terminal is in the ParkBot root directory."""
        here = Path(os.getcwd())
        root_components = {"cogs", "data"}
        sub_dirs = set([x.name for x in here.iterdir() if x.is_dir()])
        intersection = sub_dirs.intersection(root_components)
        if root_components == intersection:
            return True
        return False
        
    def findFFMPEG(self, operating_system:str) -> Path | None:
        pass
    

class WindowsDependencyHandler(ExternalDependencyHandler):

    def __init__(self, operating_sys):
        if operating_sys != "windows":
            raise OSError(f"Setup Handler spawned the wrong version of it's depedency handler. Please try to run the setup.sh script again.")
        self.operating_sys = operating_sys

    def findFFMPEG(self) -> Path | None:
        """Returns the path to 'ffmpeg.exe' if it exists in `C:\\Users\\<user>\\` or `C:\\Program Files\\`"""
        username = os.getlogin()
        user_home = Path("C:/Users") / username
        for root, dir, files in os.walk(user_home):
            if "ffmpeg.exe" in files:
                return Path(root) / "ffmpeg.exe"
        for root, dir, files in os.walk("C:/Program Files"):
            if "ffmpeg.exe" in files:
                return Path(root) / "ffmpeg.exe"
        return None

class LinuxDependencyHandler(ExternalDependencyHandler):

    def __init__(self, operating_sys):
        if operating_sys != "linux":
            raise OSError(f"Setup Handler spawned the wrong version of it's depedency handler. Please try to run the setup.sh script again.")

    def getFFMPEGPathLinux(self) -> Path | None:
        username = os.getlogin()
        user_home = Path("C:/Users") / username
    

class FFMPEGDownloader:
    """Finds out the appropriate version of FFMPEG to install on a system."""
    
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
    

    def __init__(self, os:str):
        self.operating_sys = os
        self.builds = self.getBuilds()
        # download proper version then download NSSM
        self.best_match = ""


    def getDownloadLink(self, platform:str) -> str:
        """Returns the most appropriate FFMPEG download link for a user's operating system."""
        
    
if __name__ == "__main__":
    handler = HandlerFactory.getHandler()



