from json import dumps

class AnsibleConfig:
    def __init__(self):
        self.data = self.update_config()

    @staticmethod
    def update_config():
        def remove_extra_char(content: list):
            new_data = []
            for line in content:
                if line.strip() != '':
                    new_data.append(line.strip())
            return new_data

        def ignore_comments(content: list):
            new_data = []
            for line in content:
                if line.startswith('#'):
                    pass
                else:
                    new_data.append(line)
            return new_data

        def format_all(content: list):
            new_data = {}
            last_key = None
            counter = 0
            for line in content:
                if line.startswith("["):
                    last_key = line[1:-1]
                    new_data[last_key] = {}
                else:
                    new_data[last_key][counter] = line
                    counter += 1
            return new_data

        with open(file="/etc/ansible/hosts", mode='r', encoding="utf-8") as f:
            all_datas = f.readlines()

        all_datas = remove_extra_char(content=all_datas)
        all_datas = ignore_comments(content=all_datas)
        all_datas = format_all(content=all_datas)
        return all_datas

    def get_devices_vars(self, device: str):
        new_data = {}
        data = self.data[f"{device}:vars"]
        for element in data:
            key = str(data[element]).split("=")[0].strip()
            value = "=".join(str(data[element]).split("=")[1::]).strip()
            new_data[key] = value
        return new_data