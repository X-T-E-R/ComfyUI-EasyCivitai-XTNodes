from civitaiNodes.MyUtils.civitaiModelInfo import ModelInfo
from civitaiNodes.MyUtils.ui_utils import load_image_from_url
from civitaiNodes.config import config
from comfy.sd import load_lora_for_models, load_checkpoint_guess_config
from comfy.utils import load_torch_file
import folder_paths

def append_lora_stack(lora_stack, lora_name, lora_weight, clip_weight):
    if lora_stack is None:
        lora_stack = []
    lora_stack.append(
        (
            lora_name,
            lora_weight,
            clip_weight,
        )
    )
    return lora_stack

def get_ui_images(image_urls):
    if len(image_urls) == 0:
        return {}
    elif len(image_urls) > config.max_preview_images:
        image_urls = image_urls[: config.max_preview_images]
    previews = []
    for image_url in image_urls:
        _, image_info_dict, _,_ = load_image_from_url(image_url)
        previews.append(image_info_dict)
    return previews

def make_result_dict(result, preview_images, modelinfo: ModelInfo, is_same_url: bool):
    result_dict = {
        "result": result,
        "ui": {
            "text": [modelinfo.summary if modelinfo is not None else "Could not find model info in Civitai"],
        },
    }
    if preview_images and not is_same_url and modelinfo is not None:
        result_dict["ui"]["images"] = get_ui_images(modelinfo.image_urls)
    
    return result_dict

class CheckpointLoaderSimpleWithPreviews:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model_name": (folder_paths.get_filename_list("checkpoints"),),
                "preview_images": ("BOOLEAN", {"default": True}),
            }
        }

    RETURN_TYPES = ("MODEL", "CLIP", "VAE", "STRING")
    RETURN_NAMES = ("MODEL", "CLIP", "VAE", "summary(Text)")
    FUNCTION = "load_checkpoint"
    CATEGORY = "loaders/With Previews"
    history = None
    modelinfo : ModelInfo = None

    def load_checkpoint(self, model_name, preview_images):
        model_path = folder_paths.get_full_path("checkpoints", model_name)
        could_find_model_info = True
        try:
            self.modelinfo = ModelInfo(filepath=model_path)
        except:
            could_find_model_info = False
            self.modelinfo = None

        out = load_checkpoint_guess_config(
            model_path,
            output_vae=True,
            output_clip=True,
            embedding_directory=folder_paths.get_folder_paths("embeddings"),
        )
        
        if could_find_model_info:
            result = out[:3] + (self.modelinfo.summary,)
            try:
                return make_result_dict(result, preview_images, self.modelinfo, self.history == model_name)
            finally:
                self.history = model_name
        else:
            result = out[:3] + ("Could not find model info in Civitai",)
            return make_result_dict(result, preview_images, self.modelinfo, self.history == model_name)

class LoraLoaderWithPreviews:
    def __init__(self):
        self.loaded_lora = None

    @classmethod
    def INPUT_TYPES(s):
        return {
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
    CATEGORY = "loaders/With Previews"

    def load_lora(
        self,
        model,
        clip,
        model_name,
        strength_model,
        strength_clip,
        append_loraname_if_empty,
        preview_images,
    ):
        model_path = folder_paths.get_full_path("loras", model_name)
        could_find_model_info = True
        try:
            self.modelinfo = ModelInfo(filepath=model_path)
        except:
            could_find_model_info = False
            self.modelinfo = None


        civitai_trigger_words = self.modelinfo.trainedWords if could_find_model_info else []

        if len(civitai_trigger_words) == 0:
            if append_loraname_if_empty:
                civitai_trigger_words = [self.modelinfo.rawFilename.split(".")[0]] if could_find_model_info else [model_name]

        lora = None
        if self.loaded_lora is not None:
            if self.loaded_lora[0] == model_path:
                lora = self.loaded_lora[1]
            else:
                temp = self.loaded_lora
                self.loaded_lora = None
                del temp

        if lora is None:
            lora = load_torch_file(model_path, safe_load=True)
            self.loaded_lora = (model_path, lora)

        model_lora, clip_lora = load_lora_for_models(
            model, clip, lora, strength_model, strength_clip
        )

        result = (
            model_lora,
            clip_lora,
            civitai_trigger_words,
            self.modelinfo.summary if could_find_model_info else "Could not find model info in Civitai"
        )


        try:
            return make_result_dict(result, preview_images, self.modelinfo, self.history == model_name)
        finally:
            self.history = model_name


class LoraLoaderStackedWithPreviews:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "model_name": (folder_paths.get_filename_list("loras"),),
                "lora_weight": (
                    "FLOAT",
                    {"default": 1.0, "min": -10.0, "max": 10.0, "step": 0.01},
                ),
                "bypass" : ("BOOLEAN", {"default": False}),
                "append_loraname_if_empty": ("BOOLEAN", {"default": False}),
                "preview_images": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "lora_stack": ("LORA_STACK",),
            },
        }

    RETURN_TYPES = (
        "LORA_STACK",
        "LIST",
        "STRING",
    )
    RETURN_NAMES = (
        "LORA_STACK",
        "civitai_trigger_words",
        "summary(Text)",
    )
    FUNCTION = "set_stack"
    CATEGORY = "loaders/With Previews"

    history = None
    modelinfo : ModelInfo = None

    def set_stack(
        self,
        model_name,
        lora_weight,
        append_loraname_if_empty,
        preview_images,
        lora_stack=None,
        bypass=False,
    ):
        clip_weight = lora_weight
        
        model_path = folder_paths.get_full_path("loras", model_name)
        could_find_model_info = True
        try:
            self.modelinfo = ModelInfo(filepath=model_path)
        except:
            could_find_model_info = False
            self.modelinfo = None

        civitai_trigger_words = self.modelinfo.trainedWords if could_find_model_info else []

        if len(civitai_trigger_words) == 0:
            if append_loraname_if_empty:
                civitai_trigger_words = [self.modelinfo.rawFilename.split(".")[0]] if could_find_model_info else [model_name]

        if not bypass:
            loras = append_lora_stack(lora_stack, model_name, lora_weight, clip_weight)
        else:
            loras = lora_stack
            civitai_trigger_words = []

        result = (
            loras,
            civitai_trigger_words,
            self.modelinfo.summary if could_find_model_info else "Could not find model info in Civitai"
        )



        try:
            return make_result_dict(result, preview_images, self.modelinfo, self.history == model_name)
        finally:
            self.history = model_name


class LoraLoaderStackedAdvancedWithPreviews:
    @classmethod
    def INPUT_TYPES(s):
        return {
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
                "bypass" : ("BOOLEAN", {"default": False}),
                "append_loraname_if_empty": ("BOOLEAN", {"default": False}),
                "preview_images": ("BOOLEAN", {"default": True}),
            },
            "optional": {
                "lora_stack": ("LORA_STACK",),
            },
        }

    RETURN_TYPES = (
        "LORA_STACK",
        "LIST",
        "STRING",
    )
    RETURN_NAMES = (
        "LORA_STACK",
        "civitai_trigger_words",
        "summary(Text)",
    )
    FUNCTION = "set_stack"
    CATEGORY = "loaders/With Previews"

    history = None
    modelinfo : ModelInfo = None

    def set_stack(
        self,
        model_name,
        lora_weight,
        clip_weight,
        append_loraname_if_empty,
        preview_images,
        lora_stack=None,
        bypass=False,
    ):
        model_path = folder_paths.get_full_path("loras", model_name)
        could_find_model_info = True
        try:
            self.modelinfo = ModelInfo(filepath=model_path)
        except:
            could_find_model_info = False
            self.modelinfo = None

        civitai_trigger_words = self.modelinfo.trainedWords if could_find_model_info else []

        if len(civitai_trigger_words) == 0:
            if append_loraname_if_empty:
                civitai_trigger_words = [self.modelinfo.rawFilename.split(".")[0]] if could_find_model_info else [model_name]

        if not bypass:
            loras = append_lora_stack(lora_stack, model_name, lora_weight, clip_weight)
        else:
            loras = lora_stack
            civitai_trigger_words = []

        result = (
            loras,
            civitai_trigger_words,
            self.modelinfo.summary if could_find_model_info else "Could not find model info in Civitai"
        )

        try:
            return make_result_dict(result, preview_images, self.modelinfo, self.history == model_name)
        finally:
            self.history = model_name


# A dictionary that contains all nodes you want to export with their names
# NOTE: names should be globally unique
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
