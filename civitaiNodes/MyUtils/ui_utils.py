import numpy as np
import torch
from PIL import Image

import folder_paths


import hashlib
import os
from pathlib import Path
from typing import List
import io
import base64
from PIL import Image, ImageOps
import requests
import shutil
from codetiming import Timer

def get_temp_image_path(url: str, cache_dir: Path = None, format="png") -> Path:
    if cache_dir is None:
        cache_dir = Path(folder_paths.get_output_directory()) / "http_image_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()
    cache_file = cache_dir / f"{url_hash}.{format}"
    return cache_file

@Timer(text="load_image_from_url cost time: {seconds:.1f} seconds")
def load_image_from_url(url: str) -> tuple[Image.Image, dict, str, str]:
    """Load an image from a URL.
    
    Args:
        url: The URL of the image.
    
    Returns:
        A tuple of the image, ComfyUI data, the file format, and the image path.
    """

    images = []
    masks = []

    # Ensure cache directory exists

    need_to_save = True
    image_format = "png"

    try:
        suffix = url.split(".")[-1].lower()
        image_format = suffix 
    except:
        pass
    if url.startswith("http"):
        url = remove_condition_in_url(url)
    save_path = get_temp_image_path(url, format=image_format)


    if url.startswith("data:image/"):
        i = Image.open(io.BytesIO(base64.b64decode(url.split(",")[1])))
    elif url.startswith("file://"):
        url = url[7:]
        if not os.path.isfile(url):
            raise Exception(f"File {url} does not exist")
        i = Image.open(url)
    elif url.startswith("http://") or url.startswith("https://"):
        # Generate a cache file name based on the URL
        if os.path.isfile(save_path):
            # Load from cache
            i = Image.open(save_path)
            need_to_save = False
        else:
            # Download the image
            response = requests.get(url, timeout=5)
            if response.status_code != 200:
                raise Exception(response.text)
            with open(save_path, "wb") as file:
                file.write(response.content)
            i = Image.open(io.BytesIO(response.content))
            need_to_save = False

    elif url == "":
        return None
    else:
        url = folder_paths.get_annotated_filepath(url)
        if not os.path.isfile(url):
            raise Exception(f"Invalid url: {url}")

        i = Image.open(url)
        

    return (
        i,
        {
            "filename": save_path.name,
            "subfolder": "http_image_cache",
            "type": "output",
        },
        image_format,
        str(save_path.resolve()),
    )

import json

from urllib.parse import urlparse, urlunparse

def remove_condition_in_url(url: str) -> str:
    # 从URL中删除宽度等于的参数
    # https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/8eb19f79-6163-4ade-91ec-be4bac453910/width=450/8547284.jpeg
    # -> https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/8eb19f79-6163-4ade-91ec-be4bac453910/original=true/8547284.jpeg
    
    url_parse_result = list(urlparse(url))
    if not "civitai.com" in url_parse_result[1]:
        return url
    url_parts = url_parse_result[2].split("/")
    if len(url_parts) <= 2:
        return url
    else:
        if "=" in url_parts[-2]:
            url_parts[-2] = "original=true"
            url_parse_result[2] = "/".join(url_parts)
            return urlunparse(url_parse_result)
        else:
            return url


def get_metadata_from_file(filepath: str) -> dict:
    with open(filepath, "rb") as file:
        # https://github.com/huggingface/safetensors#format
        # 8 bytes: N, an unsigned little-endian 64-bit integer, containing the size of the header
        header_size = int.from_bytes(file.read(8), "little", signed=False)

        if header_size <= 0:
            raise BufferError("Invalid header size")

        header = file.read(header_size)
        if header_size <= 0:
            raise BufferError("Invalid header")

        header_json = json.loads(header)
        return header_json["__metadata__"] if "__metadata__" in header_json else {}



def get_metadata_from_url(url: str) -> dict:
    image, _ , _, save_path = load_image_from_url(url)
    return get_metadata_from_file(save_path)


if __name__ == "__main__":
    url = "https://image.civitai.com/xG1nkqKTMzGDvpLrqFT7WA/3488411f-4ed7-43f8-8b9e-abe91e3ed78e/original=true/00365-965542718.jpeg"
    import requests
    response = requests.get(url)
    with open("test.jpeg", "wb") as file:
        file.write(response.content)
    print(get_metadata_from_url(url))
