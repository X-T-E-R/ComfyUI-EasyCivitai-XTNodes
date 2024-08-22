from civitaiNodes.MyUtils.civitaiModelInfo import ModelInfo
from civitaiNodes.MyUtils.ui_utils import load_image_from_url
from civitaiNodes.config import config
from comfy.sd import load_lora_for_models, load_checkpoint_guess_config
from comfy.utils import load_torch_file
import folder_paths

def append_lora_stack(lora_stack, lora_name, lora_weight, clip_weight):
    if lora_stack is None:
        lora_stack = []
    lora_stack.append((lora_name, lora_weight, clip_weight,))
    return lora_stack

def get_ui_images(image_urls):
    if len(image_urls) == 0:
        return {}
    elif len(image_urls) > config.max_preview_images:
        image_urls = image_urls[:config.max_preview_images]
    previews = []
    for image_url in image_urls:
        _, image_info_dict, _, _ = load_image_from_url(image_url)
        previews.append(image_info_dict)
    return previews

def make_result_dict(result, preview_images, modelinfo: ModelInfo, is_same_url: bool):
    result_dict = {
        "result": result,
        "ui": {
            "text": [modelinfo.summary],
        },
    }
    if preview_images and not is_same_url:
        result_dict["ui"]["images"] = get_ui_images(modelinfo.image_urls)
    return result_dict

class CivitaiCheckpointLoaderSimple:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "url": (
                    "STRING",
                    {
                        "default": "https://civitai.com/models/288584?modelVersionId=324619",
                    },
                ),
                "preview_images": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP", "VAE", "STRING")
    RETURN_NAMES = ("MODEL", "CLIP", "VAE", "summary(Text)")
    FUNCTION = "load_checkpoint"
    CATEGORY = "loaders/Civitai"
    modelinfo: ModelInfo = None

    def load_checkpoint(self, url, preview_images):

        self.modelinfo = ModelInfo(url)

        if not self.modelinfo.finish_downloaded:
            self.modelinfo.download()
        ckpt_path = str(self.modelinfo.full_path)
        out = load_checkpoint_guess_config(
            ckpt_path,
            output_vae=True,
            output_clip=True,
            embedding_directory=folder_paths.get_folder_paths("embeddings"),
        )
        result = out[:3] + (self.modelinfo.summary,)
        try:
            return make_result_dict(result, preview_images, self.modelinfo, self.history == url)
        finally:
            self.history = url

class CivitaiLoraLoader:
    def __init__(self):
        self.loaded_lora = None

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": { 
                "model": ("MODEL",),
                "clip": ("CLIP", ),
                "url": ("STRING",{"default": "https://civitai.com/models/352581?modelVersionId=705894",}),
                "strength_model": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "strength_clip": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "append_loraname_if_empty": ("BOOLEAN", {"default": False}),
                "preview_images": ("BOOLEAN", {"default": True}),
            }
        }
    
    loaded_lora = None
    history = None
    modelinfo : ModelInfo = None

    RETURN_TYPES = ("MODEL", "CLIP", "LIST", "STRING")
    RETURN_NAMES = ("MODEL", "CLIP", "civitai_trigger_words", "summary(Text)")
    FUNCTION = "load_lora"
    CATEGORY = "loaders/Civitai"

    def load_lora(self, model, clip, url, strength_model, strength_clip, append_loraname_if_empty, preview_images):
        self.modelinfo = ModelInfo(url)

        if not self.modelinfo.finish_downloaded:
            self.modelinfo.download()
        
        civitai_trigger_words = self.modelinfo.trainedWords

        if len(civitai_trigger_words) == 0:
            if append_loraname_if_empty:
                civitai_trigger_words = [self.modelinfo.rawFilename.split(".")[0]]

        lora_path = str(self.modelinfo.full_path)
        lora = None
        if self.loaded_lora is not None:
            if self.loaded_lora[0] == lora_path:
                lora = self.loaded_lora[1]
            else:
                temp = self.loaded_lora
                self.loaded_lora = None
                del temp

        if lora is None:
            lora = load_torch_file(lora_path, safe_load=True)
            self.loaded_lora = (lora_path, lora)

        model_lora, clip_lora = load_lora_for_models(model, clip, lora, strength_model, strength_clip)
  
        result = (model_lora, clip_lora, civitai_trigger_words, self.modelinfo.summary)
        
        try:
            return make_result_dict(result, preview_images, self.modelinfo, self.history == url)
        finally:
            self.history = url

class CivitaiLoraLoaderStacked:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
               "url": ("STRING",{"default": "https://civitai.com/models/352581?modelVersionId=705894",}),
               "lora_weight": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
               "bypass" : ("BOOLEAN", {"default": False}),
               "append_loraname_if_empty": ("BOOLEAN", {"default": False}),
               "preview_images": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "lora_stack": ("LORA_STACK", ),
            }
        }

    RETURN_TYPES = ("LORA_STACK", "LIST", "STRING")
    RETURN_NAMES = ("LORA_STACK", "civitai_trigger_words", "summary(Text)")
    FUNCTION = "set_stack"
    CATEGORY = "loaders/Civitai"
    
    history = None
    modelinfo : ModelInfo = None

    def set_stack(self, url, lora_weight, append_loraname_if_empty, preview_images, lora_stack=None, bypass=False):
        self.modelinfo = ModelInfo(url)

        if not self.modelinfo.finish_downloaded:
            self.modelinfo.download()
        
        civitai_trigger_words = self.modelinfo.trainedWords
        
        if len(civitai_trigger_words) == 0:
            if append_loraname_if_empty:
                civitai_trigger_words = [self.modelinfo.rawFilename.split(".")[0]]

        lora_name = self.modelinfo.relative_path
        if not bypass:
            loras = append_lora_stack(lora_stack, lora_name, lora_weight, 1.0)
        else:
            loras = lora_stack
            civitai_trigger_words = []

        result = (loras, civitai_trigger_words, self.modelinfo.summary)
        
        try:
            return make_result_dict(result, preview_images, self.modelinfo, self.history == url)
        finally:
            self.history = url

class CivitaiLoraLoaderStackedAdvanced:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
               "url": ("STRING",{"default": "https://civitai.com/models/352581?modelVersionId=705894",}),
               "lora_weight": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
               "clip_weight": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
               "bypass" : ("BOOLEAN", {"default": False}),
               "append_loraname_if_empty": ("BOOLEAN", {"default": False}),
               "preview_images": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "lora_stack": ("LORA_STACK", ),
            }
        }

    RETURN_TYPES = ("LORA_STACK", "LIST", "STRING")
    RETURN_NAMES = ("LORA_STACK", "civitai_trigger_words", "summary(Text)")
    FUNCTION = "set_stack"
    CATEGORY = "loaders/Civitai"
    
    history = None
    modelinfo : ModelInfo = None

    def set_stack(self, url, lora_weight, clip_weight, append_loraname_if_empty, preview_images, lora_stack=None, bypass=False):
        self.modelinfo = ModelInfo(url)

        if not self.modelinfo.finish_downloaded:
            self.modelinfo.download()
        
        civitai_trigger_words = self.modelinfo.trainedWords

        if len(civitai_trigger_words) == 0:
            if append_loraname_if_empty:
                civitai_trigger_words = [self.modelinfo.rawFilename.split(".")[0]]

        lora_name = self.modelinfo.relative_path
        if not bypass:
            loras = append_lora_stack(lora_stack, lora_name, lora_weight, clip_weight)
        else:
            loras = lora_stack
            civitai_trigger_words = []

        result = (loras, civitai_trigger_words, self.modelinfo.summary)
        
        try:
            return make_result_dict(result, preview_images, self.modelinfo, self.history == url)
        finally:
            self.history = url


# A dictionary that contains all nodes you want to export with their names
# NOTE: names should be globally unique
NODE_CLASS_MAPPINGS = {
    "CivitaiCheckpointLoaderSimple": CivitaiCheckpointLoaderSimple,
    "CivitaiLoraLoader": CivitaiLoraLoader,
    "CivitaiLoraLoaderStacked": CivitaiLoraLoaderStacked,
    "CivitaiLoraLoaderStackedAdvanced": CivitaiLoraLoaderStackedAdvanced
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "CivitaiCheckpointLoaderSimple": "Civitai Checkpoint Loader (XTNodes)",
    "CivitaiLoraLoader": "Civitai Lora Loader (XTNodes)",
    "CivitaiLoraLoaderStacked" : "Civitai Lora Loader Stacked (XTNodes)",
    "CivitaiLoraLoaderStackedAdvanced" : "Civitai Lora Loader Stacked Adv(XTNodes)"
}
