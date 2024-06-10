class SecretEnv:
    def __init__(self, filename: str = ".env"):
        self.file = filename
        self.env = {}
        self.raw = self.read()
        self.check_if_empty()
        self.conv_to_dict()

    def conv_to_dict(self) -> bool:
        for line in self.raw:
            key, value = line.strip().split("=")
            kind, ip = key.split("_")
            try:
                self.env[ip][kind] = value
            except:
                self.env[ip] = {}
                self.env[ip][kind] = value
        return True

    def read(self):
        with open(file=self.file, mode='r', encoding='utf-8') as env:
            return env.readlines()

    def get(self, name: str, key: str):
        try:
            return self.env[name][key]
        except:
            if key == "PORT":
                return 22
            else:
                raise KeyError(f"La clé {key} n'existe pas !")

    def check_if_empty(self):
        for line in self.raw:
            if len(line.strip().split("=")) == 1:
                raise ValueError(f"La valeur de la clé {line.strip().split('=')}")