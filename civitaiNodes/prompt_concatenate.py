NODE_NAME = "PythonExec"


class AnyType(str):
    """Can be connected to any data types. Credit to pythongosssss"""

    def __eq__(self, __value: object) -> bool:
        return True

    def __ne__(self, __value: object) -> bool:
        return False


ANY = AnyType("*")

DEFAULT_PROMPT_INPUT_TYPES = {
    "required": {
        "remove_duplicates": (
            "BOOLEAN",
            {"default": True},
        ),
        "whitespace_style": (
            ["keep", "space", "underscore"],
            {"default": "keep"},
        )
    },
}

def flatten_list(input_list: list) -> list:
    output_list = []
    for item in input_list:
        if isinstance(item, list):
            output_list.extend(flatten_list(item))
        else:
            output_list.append(item)
    return output_list

from typing import Any


def convert_prompt_to_string(prompt: Any) -> str:
    if isinstance(prompt, str):
        pass
    elif isinstance(prompt, list):
        prompt = ",".join(flatten_list(prompt))
    else:
        prompt = str(prompt)
    assert isinstance(prompt, str)
    for char in ["\n", "\r", "\f", "\v"]:
        prompt = prompt.replace(char, ",")
    prompt = prompt.replace("\t", " ")
    prompt = prompt.replace("，", ",")
    return prompt


def convert_prompt_to_clean_list(prompt: Any) -> list:
    prompt_str = convert_prompt_to_string(prompt)
    all_words = prompt_str.split(",")
    new_words = []
    for word in all_words:
        word = word.strip()
        if len(word) > 0:
            new_words.append(word)
    return new_words


def deduplicate_list(words: list) -> list:
    def get_clean_chars(word: str) -> str:
        # 定义允许的字符集
        allowed_chars = (
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _"
        )
        import re

        # 使用正则表达式去除不允许的字符
        return re.sub(f"[^{re.escape(allowed_chars)}]", "", word)

    existing_words = set()
    new_words = []
    for word in words:
        clean_word = get_clean_chars(word)
        # 如果清理后的单词不在现有单词集合中，则添加
        if clean_word not in existing_words:
            new_words.append(word)
            existing_words.add(clean_word)
    return new_words


def clean_prompt(
    prompt: Any,
    remove_duplicates: bool = True,
    whitespace_style: str = "space",
) -> Any:
    words = convert_prompt_to_clean_list(prompt)
    if remove_duplicates:
        words = deduplicate_list(words)
    if whitespace_style == "underscore":
        words = [word.replace(" ", "_") for word in words]
    elif whitespace_style == "space":
        words = [word.replace("_", " ") for word in words]

    return ", ".join(words)


class CleanPrompt:
    @classmethod
    def INPUT_TYPES(self):
        defalut_input_types = DEFAULT_PROMPT_INPUT_TYPES.copy()
        defalut_input_types["optional"] = {
            "prompt": (ANY,),
        }
        return defalut_input_types

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("result",)
    FUNCTION = "_clean_prompt"
    CATEGORY = "XTNodes/prompt"

    def _clean_prompt(
        self, prompt, **kwargs
    ):
        result = clean_prompt(prompt, **kwargs)
        return {
            "result": (result,),
            "ui": {
                "text": [result],
            },
        }


class PromptConcatenate:

    @classmethod
    def INPUT_TYPES(self):
        defalut_input_types = DEFAULT_PROMPT_INPUT_TYPES.copy()
        defalut_input_types["optional"] = {
            "prompt_A": (ANY,),
            "prompt_B": (ANY,),
            "prompt_C": (ANY,),
            "prompt_D": (ANY,),
            "prompt_E": (ANY,),
        }
        return defalut_input_types

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("result",)
    FUNCTION = "_concatenate_prompt"
    CATEGORY = "XTNodes/prompt"

    def _concatenate_prompt(
        self, prompt_A = None, prompt_B = None, prompt_C = None, prompt_D = None, prompt_E = None, **kwargs
    ):
        prompts = [prompt_A, prompt_B, prompt_C, prompt_D, prompt_E]
        result = ""
        for prompt in prompts:
            if prompt is not None:
                result += convert_prompt_to_string(prompt) + ", "
        result = result[:-2]
        result = clean_prompt(result, **kwargs)
        return {
            "result": (result,),
            "ui": {
                "text": [result],
            },
        }


NODE_CLASS_MAPPINGS = {
    "XTNodesCleanPrompt": CleanPrompt,
    "XTNodesPromptConcatenate": PromptConcatenate,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "XTNodesCleanPrompt": "Clean Prompt(XTNodes)",
    "XTNodesPromptConcatenate": "Prompt Concatenate(XTNodes)",
}
