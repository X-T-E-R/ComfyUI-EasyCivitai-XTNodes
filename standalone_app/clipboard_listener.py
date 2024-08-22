"""
This application is designed to automate the downloading of models from civitai.com.
It continuously monitors the clipboard for any URLs that point to civitai.com,
specifically looking for valid links. When such a link is detected, the application
automatically submits a download task to a thread pool, allowing up to 10 concurrent
downloads. This ensures efficient and timely downloading of models, streamlining
the process for the user. The application leverages multi-threading to manage multiple
downloads simultaneously, optimizing the use of system resources and providing
a seamless experience.
"""


import sys
import pathlib

sys.path.append(str(pathlib.Path(__file__).parent.parent))
# custom_nodes\ComfyUI-XTNodes-EasyCivitai\test\test_download_util.py
sys.path.append(str(pathlib.Path(__file__).parent / "/".join([".."]*3)))

from civitaiNodes.MyUtils.civitaiModelInfo import ModelInfo

import time
import pyperclip
import threading
from concurrent.futures import ThreadPoolExecutor

# 假设这是你的下载函数
def download_url(url):
    # 模拟下载任务
    try:
        info = ModelInfo(url=url)
        if not info.finish_downloaded:
            info.download()
    except:
        pass
    

def monitor_clipboard(executor):
    recent_value = ""
    while True:
        clipboard_content = pyperclip.paste()

        if clipboard_content != recent_value and "civitai.com" in clipboard_content and clipboard_content.startswith("http"):
            print(f"Detected civitai.com link: {clipboard_content}")
            # 提交下载任务给线程池
            executor.submit(download_url, clipboard_content)
            recent_value = clipboard_content

        time.sleep(0.5)

if __name__ == "__main__":
    print("Monitoring clipboard for civitai.com links...")

    # 创建线程池，最多允许10个并发任务
    with ThreadPoolExecutor(max_workers=10) as executor:
        # 启动剪切板监控线程
        clipboard_thread = threading.Thread(target=monitor_clipboard, args=(executor,))
        clipboard_thread.start()

        # 主线程等待剪切板监控线程结束
        clipboard_thread.join()
