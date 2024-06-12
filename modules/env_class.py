class SecretEnv:
    def __init__(self, filename: str = "ressources/.env"):
        self.file = filename
        self.content = self.make_dict()
    
    def make_dict(self) -> dict:
        final_dict = {}
        with open(file=self.file, mode="r", encoding="utf-8") as env:
            for device in env.readlines():
                name, pass_type = device.strip().split("=")[0].split("_")
                password = device.strip().split("=")[1]
                try:
                    final_dict[name][pass_type] = password
                except:
                    final_dict[name] = {}
                    final_dict[name][pass_type] = password
        return final_dict

    def get(self, device: str, pass_type: str) -> str:
        return self.content[device][pass_type]

    def set(self, device: str, password: str, secret: str) -> None:
        model = self.content
        model[device] = {}
        model[device]["PWD"] = password
        model[device]["SEC"] = secret
        output = ""
        for [index, value] in enumerate(model):
            if index == len(model):
                output += f"{value}_PWD={model[value]['PWD']}\n"
                output += f"{value}_SEC={model[value]['SEC']}"
            else:
                output += f"{value}_PWD={model[value]['PWD']}\n"
                output += f"{value}_SEC={model[value]['SEC']}\n"
        with open(file=self.file, mode='w', encoding="utf-8") as env:
            env.write(output)
    
    def delete_device(self, device: str):
        del self.content[device]
        output = ""
        for [index, value] in enumerate(self.content):
            if index == len(self.content):
                output += f"{value}_PWD={self.content[value]['PWD']}\n"
                output += f"{value}_SEC={self.content[value]['SEC']}"
            else:
                output += f"{value}_PWD={self.content[value]['PWD']}\n"
                output += f"{value}_SEC={self.content[value]['SEC']}\n"
        with open(file=self.file, mode='w', encoding="utf-8") as env:
            env.write(output)
        