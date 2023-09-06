import requests
import bs4 
import os
import platform
from pathlib import Path

platforms = {
    "linux": "linux",
    "windows": "windows",
    "darwin": "mac",
}

class ExternalDependencyHandler:
    """Handles downloading ParkBot dependencies that can't be installed through pip."""

    def isInProjectRoot(self) -> bool:
        """Checks if the terminal is in the ParkBot root directory."""
        here = Path(os.getcwd())
        root_components = {"cogs", "data"}
        sub_dirs = set([x.name for x in here.iterdir() if x.is_dir()])
        intersection = sub_dirs.intersection(root_components)
        if root_components == intersection:
            return True
        return False
    
    def downloadFFMPEG(self):
        # first get FFMPEG 
        parser = FFMPEGReleasesParser()
        parser.getFFMPEG()
    
    def __init__(self):
        self.root = None
        self.operating_sys:str = platforms[platform.system().lower()]
        #TODO check if FFMPEG is already installed somewhere

    

class FFMPEGReleasesParser:
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
    
    def __init__(self):
        self.builds = self.getBuilds()
        # download proper version then download NSSM


