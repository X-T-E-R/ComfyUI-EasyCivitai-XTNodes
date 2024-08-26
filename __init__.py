import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).parent))
import glob

all_py_files = pathlib.Path(__file__).parent.glob('civitaiNodes/**/*.py')

import importlib.util

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

for py_file in all_py_files:
    if pathlib.Path(py_file) == pathlib.Path(__file__):
        continue
    # print(f"Checking {py_file}")
    try:
        spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
        imported_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(imported_module)
        NODE_CLASS_MAPPINGS = {**NODE_CLASS_MAPPINGS, **imported_module.NODE_CLASS_MAPPINGS}
        NODE_DISPLAY_NAME_MAPPINGS = {**NODE_DISPLAY_NAME_MAPPINGS, **imported_module.NODE_DISPLAY_NAME_MAPPINGS}
        print(f"XTNodes: Successfully imported {py_file}")
    except Exception as e:
        # print(f"XTNodes: Failed to import {py_file} / {e}")
        pass
    
WEB_DIRECTORY = "./web"
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]