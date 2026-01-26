import inspect
import os
import sys

def _set_dir():
    frame = inspect.currentframe()
    current_dir = os.path.dirname(
        os.path.abspath(
            inspect.getfile(frame)))
    root_dir = os.path.dirname(current_dir)
    sys.path.extend([current_dir, root_dir])
    del frame
    return current_dir, root_dir