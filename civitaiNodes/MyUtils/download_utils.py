
from civitaiNodes.config import config
import subprocess

use_aria2 = config.use_aria2
aria2_extra_args = config.aria2_extra_args
max_retries = config.max_retry
retry_interval = config.retry_interval

import pathlib
import logging
logging.basicConfig(level=logging.INFO)

# 确定是否是windows系统
if pathlib.Path("C:").exists():
    # custom_nodes\ComfyUI-XTNodes-EasyCivitai\nodes\MyUtils\utils.py
    aria2_exec = str(pathlib.Path(__file__).parent.parent.parent / "aria2" / "aria2c.exe")

else:
    aria2_exec = "aria2c"

def check_aria2_installed():
    # 检查是否安装了 Aria2c
    try:
        command = [aria2_exec, "--version"]
        subprocess.run(command, check=True)
    except FileNotFoundError:
        return False
    return True

aria2_installed_flag = False
def raise_for_aria2_installed():
    global aria2_installed_flag
    if aria2_installed_flag:
        return
    # 如果没有安装 Aria2c，抛出异常
    if not check_aria2_installed():
        raise FileNotFoundError("Aria2c is not installed. Please install Aria2c first. Linux: sudo apt-get install aria2, Windows: Embeded in ./")
    else:
        aria2_installed_flag = True
        
def download_file_with_aria2(url, full_path, retries=0):
    """Download a file using aria2c with retry logic."""
    if not isinstance(full_path, pathlib.Path):
        full_path = pathlib.Path(full_path)
    full_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        aria2_exec,
        "-c",  # Continue downloading if possible
        "-x", "4",  # Use 4 connections
        "-s", "4",  # Split the file into 4 parts
        "--disable-ipv6=true" if config.disable_ipv6 else "",  # Disable IPv6
        *aria2_extra_args,  # Extra arguments
        "-d", full_path.parent,  # Directory to save the file
        "-o", full_path.name,  # Output filename
        url  # URL to download
    ]
    try:
        subprocess.run(command, check=True)
        logging.info(f"Downloaded {full_path}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Failed to download {full_path} with error: {e}, retries: {retries}")
        if retries < max_retries:
            import time
            time.sleep(retry_interval)
            logging.info(f"Retrying download of {full_path}")
            download_file_with_aria2(url, full_path, retries=retries+1)
            
import requests

def download_file_with_requests(url, full_path):
    """Download a file using requests."""
    if not isinstance(full_path, pathlib.Path):
        full_path = pathlib.Path(full_path)
    full_path.parent.mkdir(parents=True, exist_ok=True)
    response = requests.get(url)
    response.raise_for_status()
    with open(full_path, "wb") as file:
        file.write(response.content)
    logging.info(f"Downloaded {full_path}")

from urllib.parse import urlparse, parse_qs, urlencode, urlunparse   
def add_token_to_url(url: str, token: str) -> str:
    # 在URL中添加或更新token参数
    if token is None or len(token) == 0:
        return url
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    query_params['token'] = token
    new_query_string = urlencode(query_params, doseq=True)
    new_url = urlunparse(parsed_url._replace(query=new_query_string))
    return new_url

def download_file(url, full_path):
    """Download a file using aria2c or requests."""
    if config.api_endpoint in url and "token" not in url:
        url = add_token_to_url(url, config.token)
    if use_aria2:
        raise_for_aria2_installed()
        download_file_with_aria2(url, full_path)
    else:
        download_file_with_requests(url, full_path)

def get_raw_url(url):
    """Get the raw URL from redirect URL."""
    response = requests.head(url, allow_redirects=False)
    response.raise_for_status()
    if response.is_redirect:
        return response.headers["Location"]
    return url

def download_civitai_model(url, full_path):
    """Download a Civitai model from a URL."""

    url = add_token_to_url(url, config.token)
    url = get_raw_url(url)
    download_file(url, full_path)
