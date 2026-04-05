import os
import shutil
import subprocess
import sys


def open_in_default_app(path: str) -> None:
    target = os.path.abspath(path)
    if os.name == "nt":
        os.startfile(target)  # type: ignore[attr-defined]
        return
    if sys.platform == "darwin":
        subprocess.Popen(["open", target])
        return

    opener = shutil.which("xdg-open")
    if not opener:
        raise RuntimeError("Could not find xdg-open to launch files/folders.")
    subprocess.Popen([opener, target])
