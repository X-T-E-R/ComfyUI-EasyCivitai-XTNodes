from .civitaiModelInfo import ModelInfo
from .ui_utils import ExtraCivitaiParams, add_extra_output, get_summary, get_ui_images
import logging
import folder_paths
from typing import List, Tuple, Literal

def append_lora_stack(lora_stack, lora_name, lora_weight, clip_weight):
    if lora_stack is None:
        lora_stack = []
    else:
        from copy import deepcopy
        lora_stack = deepcopy(lora_stack)
    lora_stack.append((lora_name, lora_weight, clip_weight,))
    return lora_stack

# 基类，用于处理通用功能
class CivitaiBaseLoader:
    node_type : Literal["local", "remote"] = "remote"
    history = None
    modelinfo: ModelInfo = None
    extra_civitai_params: ExtraCivitaiParams = None

    def _prepare_modelinfo_by_url(self, url: str = ""):
        """创建ModelInfo对象并下载模型文件（如果尚未下载）"""
        self.node_type = "remote"
        self.modelinfo = ModelInfo(url)

        if not self.modelinfo.finish_downloaded:
            self.modelinfo.download()
            
    def _prepare_modelinfo_by_name(self, model_path: str = ""):
        """本地加载模型"""
        self.node_type = "local"
        try:
            self.modelinfo = ModelInfo(filepath=model_path)
        except:
            self.modelinfo = None
        
    
    def prepare_modelinfo(self, url: str = "", model_path :str = "", **kwargs):
        """创建ModelInfo对象并下载模型文件（如果尚未下载），并生成额外参数"""
        self.extra_civitai_params = ExtraCivitaiParams(**kwargs)
        if len(url) > 0:
            self._prepare_modelinfo_by_url(url)
        else:
            self._prepare_modelinfo_by_name(model_path)
            
    def _make_result_dict(self, result,  is_same_url: bool = False):
        """生成结果字典"""
        result_dict = {
            "result": add_extra_output(result, self.extra_civitai_params, self.modelinfo),
            "ui": {
                "text": [get_summary(self.modelinfo)],
            },
        }
        if self.modelinfo is not None:
            if self.extra_civitai_params.preview_images and not is_same_url and not self.extra_civitai_params.bypass:
                result_dict["ui"]["images"] = get_ui_images(self.modelinfo.image_urls)
        return result_dict

    def is_same_url(self, url: str):
        """判断是否是同一个url"""
        if self.modelinfo is None:
            return False
        return self.modelinfo.url == url
    
    def process_result(self, result):
        """处理结果，记录日志并更新历史"""
        try:
            return self._make_result_dict(result, self.is_same_url(self.history))
        except Exception as e:
            self.log_error(e, "Error processing result")
            raise
        finally:
            if self.modelinfo is not None:
                self.history = self.modelinfo.url if not self.extra_civitai_params.bypass else None
            else:
                self.history = None

    @staticmethod
    def log_error(e: Exception, message: str = "Error occurred"):
        """记录错误日志"""
        logging.error(f"{message}: {e}")


