import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).parent.parent))
# custom_nodes\ComfyUI-XTNodes-EasyCivitai\test\test_download_util.py
sys.path.append(str(pathlib.Path(__file__).parent / "/".join([".."]*3)))

from nodes.MyUtils.download_utils import download_file, download_file_with_aria2, download_file_with_requests, raise_for_aria2_installed, download_civitai_model

raise_for_aria2_installed()

test_file_path = pathlib.Path(__file__).parent / "a.test"
download_file("https://files.pythonhosted.org/packages/fa/07/78b8a14804c8dd607745f36f1265c609e83d076c962d4d9be4b90bde13ea/aria2p-0.12.0.tar.gz", test_file_path)


test_model_path = pathlib.Path(__file__).parent / "test_model.safe_tensor"
download_civitai_model("https://civitai.com/api/download/models/705894?type=Model&format=SafeTensor", test_model_path)

test_file_path.unlink()
test_model_path.unlink()

