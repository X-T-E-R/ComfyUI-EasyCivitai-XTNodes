from civitaiNodes.MyUtils.CivitaiBaseLoader import append_lora_stack, CivitaiBaseLoader
from civitaiNodes.MyUtils.ui_utils import add_civitai_input_dict, add_civitai_return_types, add_civitai_return_names
from comfy.sd import load_lora_for_models, load_checkpoint_guess_config
from comfy.utils import load_torch_file
import folder_paths

class CheckpointLoaderSimpleWithPreviews(CivitaiBaseLoader):
    @classmethod
    def INPUT_TYPES(cls):
        original_input = {
            "required": {
                "model_name": (folder_paths.get_filename_list("checkpoints"),),
            }
        }
        return add_civitai_input_dict(original_input)

    RETURN_TYPES = add_civitai_return_types(("MODEL", "CLIP", "VAE"))
    RETURN_NAMES = add_civitai_return_names(("MODEL", "CLIP", "VAE"))
    FUNCTION = "load_checkpoint"
    CATEGORY = "loaders/With Previews"

    def load_checkpoint(self, model_name, **kwargs):
        model_path = folder_paths.get_full_path("checkpoints", model_name)
        self.prepare_modelinfo(model_path=model_path, **kwargs)

        out = load_checkpoint_guess_config(
            model_path,
            output_vae=True,
            output_clip=True,
            embedding_directory=folder_paths.get_folder_paths("embeddings"),
        )

        result = out[:3]
        return self.process_result(result)

class LoraLoaderWithPreviews(CivitaiBaseLoader):
    def __init__(self):
        super().__init__()
        self.loaded_lora = None

    @classmethod
    def INPUT_TYPES(cls):
        original_input = {
            "required": {
                "model": ("MODEL",),
                "clip": ("CLIP",),
                "model_name": (folder_paths.get_filename_list("loras"),),
                "strength_model": (
                    "FLOAT",
                    {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01},
                ),
                "strength_clip": (
                    "FLOAT",
                    {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01},
                ),
              
            }
        }
        return add_civitai_input_dict(original_input)

    RETURN_TYPES = add_civitai_return_types(("MODEL", "CLIP"))
    RETURN_NAMES = add_civitai_return_names(("MODEL", "CLIP"))
    FUNCTION = "load_lora"
    CATEGORY = "loaders/With Previews"

    def load_lora(self, model, clip, model_name, strength_model, strength_clip, **kwargs):
        model_path = folder_paths.get_full_path("loras", model_name)
        self.prepare_modelinfo(model_path=model_path, **kwargs)
        
        lora = None
        if self.loaded_lora and self.loaded_lora[0] == model_path:
            lora = self.loaded_lora[1]
        else:
            lora = load_torch_file(model_path, safe_load=True)
            self.loaded_lora = (model_path, lora)

        model_lora, clip_lora = load_lora_for_models(model, clip, lora, strength_model, strength_clip)

        result = (model_lora, clip_lora,)
        return self.process_result(result)

class LoraLoaderStackedWithPreviews(CivitaiBaseLoader):
    @classmethod
    def INPUT_TYPES(cls):
        original_input = {
            "required": {
                "model_name": (folder_paths.get_filename_list("loras"),),
                "lora_weight": (
                    "FLOAT",
                    {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01},
                ),
                "bypass": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "lora_stack": ("LORA_STACK",),
            },
        }
        return add_civitai_input_dict(original_input)

    RETURN_TYPES = add_civitai_return_types(("LORA_STACK", ))
    RETURN_NAMES = add_civitai_return_names(("LORA_STACK", ))
    FUNCTION = "set_stack"
    CATEGORY = "loaders/With Previews"

    def set_stack(self, model_name, lora_weight, lora_stack=None, bypass=False, **kwargs):
        model_path = folder_paths.get_full_path("loras", model_name)
        self.prepare_modelinfo(model_path=model_path, **kwargs, bypass=bypass)
        
        if not bypass:
            loras = append_lora_stack(lora_stack, model_name, lora_weight, lora_weight)
        else:
            loras = lora_stack

        result = (loras, )
        return self.process_result(result)

class LoraLoaderStackedAdvancedWithPreviews(CivitaiBaseLoader):
    @classmethod
    def INPUT_TYPES(cls):
        original_input = {
            "required": {
                "model_name": (folder_paths.get_filename_list("loras"),),
                "lora_weight": (
                    "FLOAT",
                    {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01},
                ),
                "clip_weight": (
                    "FLOAT",
                    {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01},
                ),
                "bypass": ("BOOLEAN", {"default": False}),
            },
            "optional": {
                "lora_stack": ("LORA_STACK",),
            },
        }
        return add_civitai_input_dict(original_input)

    RETURN_TYPES = add_civitai_return_types(("LORA_STACK", ))
    RETURN_NAMES = add_civitai_return_names(("LORA_STACK", ))
    FUNCTION = "set_stack"
    CATEGORY = "loaders/With Previews"

    def set_stack(self, model_name, lora_weight, clip_weight, lora_stack=None, bypass=False, **kwargs):
        model_path = folder_paths.get_full_path("loras", model_name)
        self.prepare_modelinfo(model_path=model_path, **kwargs, bypass=bypass)

        if not bypass:
            loras = append_lora_stack(lora_stack, model_name, lora_weight, clip_weight)
        else:
            loras = lora_stack

        result = (loras,)
        return self.process_result(result)

# 节点类和显示名称映射
NODE_CLASS_MAPPINGS = {
    "CheckpointLoaderSimpleWithPreviews": CheckpointLoaderSimpleWithPreviews,
    "LoraLoaderWithPreviews": LoraLoaderWithPreviews,
    "LoraLoaderStackedWithPreviews": LoraLoaderStackedWithPreviews,
    "LoraLoaderStackedAdvancedWithPreviews": LoraLoaderStackedAdvancedWithPreviews,
}

# A dictionary that contains the friendly/humanly readable titles for the nodes
NODE_DISPLAY_NAME_MAPPINGS = {
    "CheckpointLoaderSimpleWithPreviews": "Load Checkpoint with Previews (XTNodes)",
    "LoraLoaderWithPreviews": "Load Lora with Previews (XTNodes)",
    "LoraLoaderStackedWithPreviews": "Load Lora Stacked with Previews (XTNodes)",
    "LoraLoaderStackedAdvancedWithPreviews": "Load Lora Stacked Advanced with Previews (XTNodes)",
}
