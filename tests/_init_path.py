from pathlib import Path
import sys


def add_path(path):
    if path not in sys.path:
        sys.path.insert(0, path)


PROJ_ROOT = Path(__file__).resolve().parents[3]
add_path(str(PROJ_ROOT))
