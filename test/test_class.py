import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).parent.parent))
# custom_nodes\ComfyUI-XTNodes-EasyCivitai\test\test_download_util.py
sys.path.append(str(pathlib.Path(__file__).parent / "/".join([".."]*3)))

from civitaiNodes.MyUtils.civitaiModelInfo import ModelInfo, remove_condition_in_url

test_image_url = "https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/8eb19f79-6163-4ade-91ec-be4bac453910/width=450/8547284.jpeg"
print(remove_condition_in_url(test_image_url))

url = "https://civitai.com/models/43965?modelVersionId=58585"
info = ModelInfo(url=url)
print(info.model_dump_json(indent=4, exclude=["images", "files"]))
print(info.subfolder)
print(info.full_path)

"custom_nodes\ComfyUI-XTNodes-EasyCivitai\test\test_class.py"

filepath = pathlib.Path(__file__).parent / ( "../" * 3)/ "models" / "loras\pony\poses\Pov Blowjob + Titjob + Handjob 2.0 - Pov B+T+handjob pony 2.0 - Pov_Blowjob__Titjob__Handjob_2.0.safetensors"

def timer(func):
    import time
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print(f"Time elapsed: {time.time() - start} seconds")
        return result
    return wrapper

@timer
def get_id_from_hash(filepath):
    info = ModelInfo(filepath=filepath)
    print(info.model_dump_json(indent=4, exclude=["images", "files"]))
    print(info.subfolder)
    print(info.summary)

get_id_from_hash(filepath)