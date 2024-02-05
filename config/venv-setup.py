import os
import platform
import subprocess
from pathlib import Path
from venv import EnvBuilder

class VenvSetupWizard:
    
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
        """Returns the path to the python executable in the `.venv` directory. Assumes it's being executed in the ParkBot root directory."""
        dir_to_search = Path(os.getcwd()) / ".venv"
        match platform.system().lower():
            case "windows":
                desired_file = "python.exe"
            case "linux":
                desired_file = "python"
            case _:
                raise OSError("Unsupported operating system.")
        for dirpath, dirs, files in os.walk(dir_to_search):
            for filename in files:
                if (desired_file == filename):
                    python_exe = Path(dirpath) / desired_file
                    if os.access(python_exe, os.X_OK):
                        return Path(dirpath) / desired_file
    
    def create_venv(self, project_root:Path) -> None:
        """Creates a virtual environment and saves the location of it's python executable."""
        venv_exists = self.is_env_created()
        if venv_exists is False:
            builder = EnvBuilder(with_pip=True)
            builder.create(project_root)
        #BUG need to make this python executable platform agnostic instead of hard coding it
        os.environ["PARKBOT_PYTHON"] = str(self.find_python())

    def is_env_created(self) -> bool:
        """Checks if a virtual environment subdirectory exists at the root level of ParkBot."""
        root_subdirs = [x.name for x in Path(os.getcwd()).iterdir() if x.is_dir()]
        match platform.system().lower():
            case "windows":
                venv_components = {"lib", "scripts", "include"}
            case "linux":
                venv_components = {"lib", "bin", "include"}
            case _:
                raise OSError("This operating system is not supported by the venv-setup wizard.")
        for path in root_subdirs:
            path = Path(path)
            sub_sub_dirs = set([x.name.lower() for x in path.iterdir() if x.is_dir()])
            intersection = sub_sub_dirs.intersection(venv_components)
            if venv_components == intersection:
                # if a venv already exists, get its python exe and store it in env variable
                return True
        return False

    def pip_install_deps(self) -> None:
        """Creates a subprocess to pip-install dependencies listed in requirements.txt."""
        subprocess.check_call([os.environ["PARKBOT_PYTHON"], "-m", "pip", "install", "-r", "requirements.txt"])

    def __init__(self):
        inRoot = self.is_in_project_root()
        if inRoot is False:
            raise FileNotFoundError(f"You must execute the setup wizard from the root directory of the ParkBot project.")
        self.root = Path(os.getcwd())
        self.env = self.root / ".venv"
        self.data_dir = self.root / "data"
        self.bank = self.data_dir / "bank.csv"
        self.threads = self.data_dir/ "threads.csv"

    def main(self):
        self.create_venv(self.env)
        self.pip_install_deps()

if  __name__ == "__main__":
    wiz = VenvSetupWizard()
    wiz.main()