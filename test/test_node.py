import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).parent.parent))
# custom_nodes\ComfyUI-XTNodes-EasyCivitai\test\test_download_util.py
sys.path.append(str(pathlib.Path(__file__).parent / "/".join([".."]*3)))

from civitaiNodes.nodes import CivitaiLoraLoaderStacked, NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

CivitaiLoraLoaderStacked()
