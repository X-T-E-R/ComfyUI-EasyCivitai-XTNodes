import requests
import pathlib
import re
from pydantic import BaseModel, Field
import json
from typing import Any, Dict
from sanitize_filename import sanitize as sanitize_filename
import blake3
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
import sys
from codetiming import Timer

from civitaiNodes.config import CivitaiConfig, config
from folder_paths import models_dir

models_folder = config.models_folder
from .download_utils import download_civitai_model
from .LazyLoadDict import LazyLoadDict


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
            # url_parts[-2] = "original=true"
            url_parts[-2] = "width=450"
            url_parse_result[2] = "/".join(url_parts)
            return urlunparse(url_parse_result)
        else:
            return url


# 映射模型类型到保存路径
type_to_savepath_map = {
    "lora": "loras",
    "checkpoint merge": "checkpoints",
    "checkpoint trained": "checkpoints",
    "checkpoint": "checkpoints",
    "motion" : "animatediff_motion_lora"
}

# 标签列表，用于分类模型
category_labels = [
    "character", "style", "celebrity", "concept", "clothing", "base model", "poses",
    "background", "tool", "buildings", "vehicle", "objects", "animal", "action", "assets"
]

def get_category(tags: list[str]) -> str:
    # 根据标签列表返回对应的类别
    for tag in tags:
        if tag in category_labels:
            return tag
    return "unknown"

class ModelVersionNotFound(Exception):
    """自定义异常，用于在指定的模型版本ID未找到时抛出"""
    pass

filepath_to_hash_map = LazyLoadDict(config.json_cache_dir / "filepath_to_hash_map.json")

def get_blake3_hash(filepath) -> str:
    hasher = blake3.blake3()  # 初始化 BLAKE3 哈希对象
    with open(filepath, "rb") as file:
        while chunk := file.read(8192):  # 分块读取文件
            hasher.update(chunk)  # 更新哈希值
    return hasher.hexdigest()

def get_ids_from_file(filepath, force_update: bool = False) -> tuple[int, int]:
    # 获取文件的Blake3哈希值并从API中获取对应的模型ID和版本ID
    if not isinstance(filepath, pathlib.Path):
        filepath = pathlib.Path(filepath)
    filepath = filepath.resolve()
    if filepath in filepath_to_hash_map:
        item = filepath_to_hash_map[filepath]
        return item["modelId"], item["modelVersionId"]
    hash = get_blake3_hash(filepath)
    url = config.api_endpoint + "/model-versions/by-hash/" + hash
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    modelId = data["modelId"]
    modelVersionId = data["id"]
    filepath_to_hash_map[filepath] = {"modelId": modelId, "modelVersionId": modelVersionId}
    return modelId, modelVersionId

def get_image_urls_from_file(filepath) -> list[str]:
    modelId, _ = get_ids_from_file(filepath)
    return ModelInfo(modelId=modelId).image_urls

def gather_prompt_list(prompt_list: list[str]) -> list[str]:
    def clean_empty(prompt : str) -> str:
        return prompt.strip()
    
    def unique_by_lower(prompt_list):
        seen = set()
        new_list = []
        for prompt in prompt_list:
            if len(prompt) == 0:
                continue
            lower = prompt.lower()
            if lower not in seen:
                seen.add(lower)
                new_list.append(prompt)
        return new_list
    
    new_prompt_list = []
    for prompt in prompt_list:
        new_prompt_list.extend(prompt.split(","))
    new_prompt_list = list(map(clean_empty, new_prompt_list))
    return unique_by_lower(new_prompt_list)



class ModelInfo(BaseModel):
    # 定义模型信息的结构
    id: int
    title: str
    type: str
    tags: list[str]
    category: str
    nsfw: bool
    versionId: int
    baseModel: str
    images: list[dict[str, Any]]
    files: list[dict[str, Any]]
    downloadUrl: str
    versionName: str
    trainedWords: list[str] = Field(default=[])
    rawFilename: str

    @staticmethod
    def check_versionId(data: Dict[str, Any], versionId: int) -> bool:
        # 检查指定版本ID是否存在于数据中
        for modelVersion in data["modelVersions"]:
            if modelVersion["id"] == versionId:
                return True
        return False

    @staticmethod
    def get_url_json(modelId: int, force_update: bool = False, versionId: int = None, config: CivitaiConfig = config) -> Dict[str, Any]:
        # 从缓存中获取模型信息JSON或通过API请求获取数据
        json_cache_path = config.json_cache_dir / f"{modelId}.json"
        if not force_update and json_cache_path.exists():
            with open(json_cache_path, "r", encoding="utf-8") as file:
                data = json.load(file)
            if versionId is None or ModelInfo.check_versionId(data, versionId):
                return data
        response = requests.get(f"{config.api_endpoint}/models/{modelId}")
        response.raise_for_status()
        data = response.json()
        with open(json_cache_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
        return data

    @staticmethod
    def get_ids_from_url(url: str) -> tuple[int, int]:
        # 从URL中提取模型ID和版本ID
        model_id = re.search(r"models/(\d+)", url).group(1)
        model_version_id = re.search(r"modelVersionId=(\d+)", url)
        return int(model_id), int(model_version_id.group(1)) if model_version_id else None

    def __init__(
        self,
        url: str | None = None,
        modelId: int | None = None,
        modelVersionId: int | None = None,
        filepath: str | None = None,
        config: CivitaiConfig = config,
        **data,
    ):
        # 初始化 ModelInfo 对象，可以通过URL或直接通过模型ID和版本ID来初始化
        if url is not None:
            modelId, modelVersionId = self.get_ids_from_url(url)
        elif filepath is not None:
            modelId, modelVersionId = get_ids_from_file(filepath)
        if modelId is not None:
            data = self.get_url_json(modelId=modelId, versionId=modelVersionId, config=config)
            parsed_model = self.parse_model_id_json(data, modelVersionId=modelVersionId)
            self.__dict__.update(parsed_model.__dict__)
            return
        super().__init__(**data)

    @property
    def url(self) -> str:
        return f"https://civitai.com/models/{self.id}?modelVersionId={self.versionId}"
    
    @property
    def filename(self) -> str:
        return f"{sanitize_filename(self.title)} - {sanitize_filename(self.versionName)} - {sanitize_filename(self.rawFilename)}"

    @property
    def subfolder(self) -> str:
        baseModel = sanitize_filename(self.baseModel).replace(" ", "")
        save_type = self.type
        if save_type == "checkpoints":
            return f"{baseModel}/"
        return f"{baseModel}/{self.category}/"

    @property
    def relative_path(self) -> str:
        # 构建文件保存路径
        return self.subfolder + self.filename

    @property
    def full_path(self) -> pathlib.Path:
        save_type = self.type
        # 获取文件的完整路径
        return models_folder / save_type / self.subfolder / self.filename

    @property
    def image_urls(self) -> list[str]:
        # 获取模型图片的URL列表
        return [image["url"] for image in self.images]

    @property
    def finish_downloaded(self) -> bool:
        full_path = self.full_path
        if pathlib.Path(str(full_path) + ".aria2").exists():
            return False
        return full_path.exists()

    @property
    def summary(self) -> str:
        result = "\n".join(
            [
                f"{self.url}",
                f"{self.title} - {self.versionName}",
                f"Type: {self.type}",
                f"Base Model: {self.baseModel}",
                f"Category: {self.category}",
                f"Tags: { ', '.join(self.tags) }",
            ]
        )
        if isinstance(self.trainedWords, list) and len(self.trainedWords) > 0:
            result += f"\nTrained Words: { ', '.join(self.trainedWords) }"
        return result

    # @Timer(text="Download Time: {seconds:.1f} seconds")
    def download(self, full_path: pathlib.Path = None):
        # 下载模型文件
        if full_path is None:
            full_path = self.full_path
        download_civitai_model(self.downloadUrl, full_path)

    @classmethod
    def parse_model_id_json(cls, data: Dict[str, Any], modelVersionId: int = None) -> "ModelInfo":
        # 从JSON数据中解析模型信息
        tags = data["tags"]
        category = get_category(tags)
        modelVersions = data["modelVersions"]
        selectedModelVersion = None
        if modelVersionId is None:
            selectedModelVersion = modelVersions[0]
        else:
            for modelVersion in modelVersions:
                if modelVersion["id"] == modelVersionId:
                    selectedModelVersion = modelVersion
                    break
        if selectedModelVersion is None:
            raise ModelVersionNotFound(f"Model version {modelVersionId} not found in {data['id']}")
        assert isinstance(selectedModelVersion, dict)
        files = selectedModelVersion["files"]
        rawFilename = ""
        for file in files:
            if file["downloadUrl"] == selectedModelVersion["downloadUrl"]:
                rawFilename = file["name"]
                
        trainedWords = selectedModelVersion.get("trainedWords", [])
        trainedWords = gather_prompt_list(trainedWords)
        
        images=selectedModelVersion["images"]
        for image in images:
            image["url"] = remove_condition_in_url(image["url"])
        
        return cls(
            id=data["id"],
            title=data["name"],
            nsfw=data["nsfw"],
            type=type_to_savepath_map.get(data["type"].lower(), data["type"]),
            tags=tags,
            category=category,
            versionId=selectedModelVersion["id"],
            versionName=selectedModelVersion["name"],
            baseModel=selectedModelVersion["baseModel"],
            images=images,
            files=files,
            downloadUrl=selectedModelVersion["downloadUrl"],
            trainedWords=trainedWords,
            rawFilename=rawFilename,
        )



if __name__ == "__main__":
    import sys
    sys.path.append(pathlib.Path(__file__).parent.parent.parent)
    # url = "https://civitai.com/models/43965?modelVersionId=58585"
    # info = ModelInfo(url=url)
    # print(info.model_dump_json(indent=4, exclude=["images", "files"]))
    # print(info.subfolder)
    # print(info.full_path)
    # print(info.image_urls)
