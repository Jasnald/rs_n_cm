# -*- coding: utf-8 -*-
# _get_plane_info.py

from ...utilitary import*
from ...imports   import*


class PlaneGetter(LoggerMixin):
    def __init__(self):
        self.json_path = None

    def load(self):
        """
        Method: load_plane_settings
        What it does: Loads plane settings from a JSON file, returns an empty dict if not found or error occurs.
        """
        json_path = self.json_path
        try:
            if os.path.isfile(json_path):
                with open(json_path, "r") as f:
                    plane_settings = json.load(f)
                    print("Plane configurations loaded from JSON.")
                return plane_settings
            else:
                print("No JSON file found. Using default settings.")
                return {}
        except Exception as e:
            print("Error loading plane settings:", e)
            return {}