#!/usr/bin/env python
# -*- coding: utf-8 -*-

#reader.py

from .imports import *

class INPWriter:
    def __init__(self, output_path: str):
        self.output_path = Path(output_path)

    def write(self, lines: List[str]) -> None:
        with open(self.output_path, "w", encoding="utf-8") as f:
            f.writelines(lines)