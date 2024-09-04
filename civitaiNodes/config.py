from dynaconf import Dynaconf
import pathlib


from folder_paths import models_dir

project_root = pathlib.Path(__file__).parent.parent

settings = Dynaconf(
    root_path=project_root,
    preload = [".secrets.toml"],
    settings_files=["settings.toml"],
)
# print(settings)


class CivitaiConfig:
    api_endpoint: str = settings.civitai.api_endpoint
    token: str = settings.civitai.get("token", "")
    json_cache_dir: pathlib.Path = pathlib.Path(__file__).parent.parent / "json_cache"
    aria2_extra_args: list[str] = settings.aria2.extra_args or []
    max_retry: int = settings.aria2.max_retry or 5
    retry_interval: int = settings.aria2.retry_interval or 15
    use_aria2: bool = "aria2" in settings.download.method if hasattr(settings, "download") else True
    disable_ipv6: bool = settings.aria2.disable_ipv6 or True
    models_folder = pathlib.Path(models_dir).resolve()
    max_preview_images: int = settings.civitai.max_preview_images or 6
    
    def __init__(self, **kwargs):
        # 初始化配置时，将传入的关键字参数赋值给实例属性
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        # 确保 json_cache_dir 目录存在
        self.json_cache_dir.mkdir(exist_ok=True)

config = CivitaiConfig()
