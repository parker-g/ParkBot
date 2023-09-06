from venv import EnvBuilder
from pathlib import Path
import subprocess
import os

class VenvSetupWizard:
    
    def isInProjectRoot(self) -> bool:
        """Checks if the terminal is in the ParkBot root directory."""
        here = Path(os.getcwd())
        root_components = {"cogs", "data"}
        sub_dirs = set([x.name for x in here.iterdir() if x.is_dir()])
        intersection = sub_dirs.intersection(root_components)
        if root_components == intersection:
            return True
        return False
    
    def createVenv(self, project_root:Path) -> None:
        """Creates a virtual environment and saves the location of it's python executable."""
        venv_exists = self.isEnvCreated()
        if venv_exists is False:
            builder = EnvBuilder(with_pip=True)
            builder.create(project_root)
        os.environ["PARKBOT_PYTHON"] = str(project_root / "Scripts" / "python.exe")

    def isEnvCreated(self) -> bool:
        """Checks if a virtual environment subdirectory exists at the root level of ParkBot."""
        root_subdirs = [x.name for x in Path(os.getcwd()).iterdir() if x.is_dir()]
        venv_components = {"lib", "scripts", "include"}
        for path in root_subdirs:
            path = Path(path)
            sub_sub_dirs = set([x.name.lower() for x in path.iterdir() if x.is_dir()])
            intersection = sub_sub_dirs.intersection(venv_components)
            if venv_components == intersection:
                # if a venv already exists, get its python exe and store it in env variable
                return True
        return False

    def pipInstallDeps(self) -> None:
        """Creates a subprocess to pip-install dependencies listed in requirements.txt."""
        subprocess.check_call([os.environ["PARKBOT_PYTHON"], "-m", "pip", "install", "-r", "requirements.txt"])

    def __init__(self):
        inRoot = self.isInProjectRoot()
        if inRoot is False:
            raise FileNotFoundError(f"You must execute the setup wizard from the root directory of the ParkBot project.")
        self.root = Path(os.getcwd())
        self.env = self.root / ".venv"
        self.data_dir = self.root / "data"
        self.bank = self.data_dir / "bank.csv"
        self.threads = self.data_dir/ "threads.csv"

    def main(self):
        self.createVenv(self.env)
        self.pipInstallDeps()

if  __name__ == "__main__":
    wiz = VenvSetupWizard()
    wiz.main()