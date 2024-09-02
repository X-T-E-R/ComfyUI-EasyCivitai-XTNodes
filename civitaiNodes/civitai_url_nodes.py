from civitaiNodes.MyUtils.CivitaiBaseLoader import append_lora_stack,  CivitaiBaseLoader
from civitaiNodes.MyUtils.ui_utils import add_civitai_input_dict,  add_civitai_return_types, add_civitai_return_names
from comfy.sd import load_lora_for_models, load_checkpoint_guess_config
from comfy.utils import load_torch_file
import folder_paths

# 检查点加载器类
class CivitaiCheckpointLoaderSimple(CivitaiBaseLoader):
    @classmethod
    def INPUT_TYPES(cls):
        original_input = {
            "required": {
                "url": (
                    "STRING",
                    {
                        "default": "https://civitai.com/models/288584?modelVersionId=324619",
                    },
                ),
            }
        }
        return add_civitai_input_dict(original_input)

    RETURN_TYPES = add_civitai_return_types(("MODEL", "CLIP", "VAE"))
    RETURN_NAMES = add_civitai_return_names(("MODEL", "CLIP", "VAE"))
    FUNCTION = "load_checkpoint"
    CATEGORY = "loaders/Civitai"

    def load_checkpoint(self, url: str, **kwargs) -> dict:
        self.prepare_modelinfo(url = url, **kwargs)

        ckpt_path = str(self.modelinfo.full_path)
        out = load_checkpoint_guess_config(
            ckpt_path,
            output_vae=True,
            output_clip=True,
            embedding_directory=folder_paths.get_folder_paths("embeddings"),
        )
        result = out[:3]
        return self.process_result(result)

# Lora加载器类
class CivitaiLoraLoader(CivitaiBaseLoader):
    def __init__(self):
        self.loaded_lora = None

    @classmethod
    def INPUT_TYPES(cls):
        original_input = {
            "required": { 
                "model": ("MODEL",),
                "clip": ("CLIP", ),
                "url": ("STRING",{"default": "https://civitai.com/models/352581?modelVersionId=705894",}),
                "strength_model": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
                "strength_clip": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
            }
        }
        return add_civitai_input_dict(original_input)
    
    RETURN_TYPES = add_civitai_return_types(("MODEL", "CLIP"))
    RETURN_NAMES = add_civitai_return_names(("MODEL", "CLIP"))
    FUNCTION = "load_lora"
    CATEGORY = "loaders/Civitai"

    def load_lora(self, model, clip, url, strength_model, strength_clip, **kwargs) -> dict:
        self.prepare_modelinfo(url = url, **kwargs)

        lora_path = str(self.modelinfo.full_path)
        lora = None
        if self.loaded_lora and self.loaded_lora[0] == lora_path:
            lora = self.loaded_lora[1]
        else:
            lora = load_torch_file(lora_path, safe_load=True)
            self.loaded_lora = (lora_path, lora)

        model_lora, clip_lora = load_lora_for_models(model, clip, lora, strength_model, strength_clip)
        result = (model_lora, clip_lora)
        return self.process_result(result)

# 堆叠Lora加载器类
class CivitaiLoraLoaderStacked(CivitaiBaseLoader):
    @classmethod
    def INPUT_TYPES(cls):
        original_input = {
            "required": {
               "url": ("STRING",{"default": "https://civitai.com/models/352581?modelVersionId=705894",}),
               "lora_weight": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
               "bypass" : ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "lora_stack": ("LORA_STACK", ),
            }
        }
        return add_civitai_input_dict(original_input)

    RETURN_TYPES = add_civitai_return_types(("LORA_STACK",))
    RETURN_NAMES = add_civitai_return_names(("LORA_STACK",))
    FUNCTION = "set_stack"
    CATEGORY = "loaders/Civitai"

    def set_stack(self, url, lora_weight, lora_stack=None, bypass=False, **kwargs) -> dict:
        self.prepare_modelinfo(url = url, **kwargs, bypass=bypass)

        lora_name = self.modelinfo.relative_path
        loras = lora_stack if bypass else append_lora_stack(lora_stack, lora_name, lora_weight, 1.0)
        result = (loras,)
        return self.process_result(result)

# 高级堆叠Lora加载器类
class CivitaiLoraLoaderStackedAdvanced(CivitaiBaseLoader):
    @classmethod
    def INPUT_TYPES(cls):
        original_input = {
            "required": {
               "url": ("STRING",{"default": "https://civitai.com/models/352581?modelVersionId=705894",}),
               "lora_weight": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
               "clip_weight": ("FLOAT", {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01}),
               "bypass" : ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "lora_stack": ("LORA_STACK", ),
            }
        }
        return add_civitai_input_dict(original_input)

    RETURN_TYPES = add_civitai_return_types(("LORA_STACK",))
    RETURN_NAMES = add_civitai_return_names(("LORA_STACK",))
    FUNCTION = "set_stack"
    CATEGORY = "loaders/Civitai"

    def set_stack(self, url, lora_weight, clip_weight, lora_stack=None, bypass=False, **kwargs) -> dict:
        self.prepare_modelinfo(url = url, **kwargs, bypass=bypass)

        lora_name = self.modelinfo.relative_path
        loras = lora_stack if bypass else append_lora_stack(lora_stack, lora_name, lora_weight, clip_weight)
        result = (loras,)
        return self.process_result(result)


# 节点类和显示名称映射
NODE_CLASS_MAPPINGS = {
    "CivitaiCheckpointLoaderSimple": CivitaiCheckpointLoaderSimple,
    "CivitaiLoraLoader": CivitaiLoraLoader,
    "CivitaiLoraLoaderStacked": CivitaiLoraLoaderStacked,
    "CivitaiLoraLoaderStackedAdvanced": CivitaiLoraLoaderStackedAdvanced
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CivitaiCheckpointLoaderSimple": "Civitai Checkpoint Loader (XTNodes)",
    "CivitaiLoraLoader": "Civitai Lora Loader (XTNodes)",
    "CivitaiLoraLoaderStacked" : "Civitai Lora Loader Stacked (XTNodes)",
    "CivitaiLoraLoaderStackedAdvanced" : "Civitai Lora Loader Stacked Adv(XTNodes)"
}
