from json import load, dumps



class JsonData:
    def __init__(self, filename: str = "ressources/datas.json"):
        self.file = filename
        self.content = self.read_json()

    def read_json(self) -> dict:
        with open(file=self.file, mode="r", encoding="utf-8") as json:
            return load(json)

    def get(self, device: str, key: str, data_type: str = "devices") -> str:
        return self.content[data_type][device][key]

    def set(self, new_dict: dict) -> None:
        with open(file=self.file, mode="w", encoding="utf-8") as json:
            json.write(dumps(new_dict, indent=4))
        self.content = self.read_json()

    def device_exist(self, ip: str):
        for hostname in self.content["devices"]:
            if ip in self.content["devices"][hostname]["ip"]:
                return True
        return False
    
    def get_hostname(self, ip: str):
        for hostname in self.content["devices"]:
            if ip in self.content["devices"][hostname]["ip"]:
                return hostname
    
    def delete_device(self, key: str):
        if key in self.content["devices"]:
            del self.content["devices"][key]
            self.set(new_dict=self.content)