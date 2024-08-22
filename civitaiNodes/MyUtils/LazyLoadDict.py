import json
import os

class LazyLoadDict:
    def __init__(self, filepath):
        self.filepath = filepath
        self._data = {}

    def _load(self):
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._data.update(data)
            except :
                pass
        

    def save(self):
        with open(self.filepath, 'w', encoding='utf-8') as f:
            json.dump(self._data, f, ensure_ascii=False, indent=4)

    def _convert_key(self, key):
        # 将 key 转换为字符串类型
        return str(key)

    def __setitem__(self, key, value):
        key = self._convert_key(key)
        self._load()  # 每次操作前加载最新数据
        self._data[key] = value
        self.save()  # 每次操作后保存数据

    def __delitem__(self, key):
        key = self._convert_key(key)
        self._load()  # 每次操作前加载最新数据
        del self._data[key]
        self.save()  # 每次操作后保存数据

    def update(self, *args, **kwargs):
        self._load()  # 每次操作前加载最新数据
        for key, value in dict(*args, **kwargs).items():
            self._data[self._convert_key(key)] = value
        self.save()  # 每次操作后保存数据

    def pop(self, key, default=None):
        key = self._convert_key(key)
        self._load()  # 每次操作前加载最新数据
        result = self._data.pop(key, default)
        self.save()  # 每次操作后保存数据
        return result

    def clear(self):
        self._load()  # 每次操作前加载最新数据
        self._data.clear()
        self.save()  # 每次操作后保存数据

    def __getitem__(self, key):
        key = self._convert_key(key)
        self._load()  # 每次访问时重新加载数据
        return self._data[key]

    def get(self, key, default=None):
        key = self._convert_key(key)
        self._load()  # 每次访问时重新加载数据
        return self._data.get(key, default)

    def __contains__(self, key):
        key = self._convert_key(key)
        self._load()  # 每次访问时重新加载数据
        return key in self._data

    def items(self):
        self._load()  # 每次访问时重新加载数据
        return self._data.items()

    def keys(self):
        self._load()  # 每次访问时重新加载数据
        return self._data.keys()

    def values(self):
        self._load()  # 每次访问时重新加载数据
        return self._data.values()

    def __iter__(self):
        self._load()  # 每次访问时重新加载数据
        return iter(self._data)

    def __len__(self):
        self._load()  # 每次访问时重新加载数据
        return len(self._data)
    
    def __str__(self):
        self._load()
        return str(self._data)
    
    def __repr__(self):
        self._load()
        return repr(self._data)


if __name__ == "__main__":
    # 测试
    data = LazyLoadDict('test.json')
    data['name'] = 'Tom'
    data['age'] = 18
    print(data)
    data["111"] = "222"
    data['name'] = 'Jerry'
    print(data)
    data.pop('name')
    data['age'] = 20
    print(data)
    data.update({'name': 'Alice', 'age': 22})
