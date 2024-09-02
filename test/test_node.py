import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).parent.parent))
# custom_nodes\ComfyUI-XTNodes-EasyCivitai\test\test_download_util.py
sys.path.append(str(pathlib.Path(__file__).parent / "/".join([".."]*3)))

from civitaiNodes.civitai_url_nodes import CivitaiCheckpointLoaderSimple, CivitaiBaseLoader, CivitaiLoraLoaderStacked
from civitaiNodes.local_loader_nodes import LoraLoaderStackedAdvancedWithPreviews

print(CivitaiCheckpointLoaderSimple.RETURN_NAMES)
print(CivitaiCheckpointLoaderSimple.RETURN_TYPES)

# print(CivitaiLoraLoaderStacked)