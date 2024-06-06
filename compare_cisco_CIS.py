from json import load
import csv
import getpass
import inquirer
from re import split
from paramiko import SSHClient, AutoAddPolicy


class Recommendation:
    def __init__(self, filename: str = "recommendations copy.json") -> None:
        self.filename = filename

    def read_file(self):
        with open(self.filename, "r") as file:
            return load(file)
        
def load_recommendations(json_file):
    with open(json_file, 'r') as file:
        return json.load(file)

def load_devices(filename):
    devices = []
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            devices.append({'ip': row[0], 'version': row[1]})
    return devices

def select_devices(devices):
    device_list = [f"{device['ip']} - {device['version']}" for device in devices]
    questions = [
        inquirer.Checkbox('selected_devices',
                          message="Sélectionnez les appareils à sécuriser",
                          choices=device_list)
    ]
    answers = inquirer.prompt(questions)
    selected_devices = [devices[device_list.index(item)] for item in answers['selected_devices']]
    return selected_devices

def get_credentials():
    username = input("Entrez votre nom d'utilisateur: ")
    password = getpass.getpass(prompt="Entrez votre mot de passe: ")
    return username, password

    
class SSH:
    """
    La classe SSH permet d'instancier une connexion SSH, de s'y connecter
    et d'y exécuter des commandes !
    """

    def __init__(self):
        self.instance = SSHClient()
        self.add_key
        self.connect_to_ssh

    @property
    def credentials(self):
        with open('credentials.json', 'r') as cred:
            cred = load(cred)['ssh']
            return cred['domain'], int(cred['port']), cred['username'], cred['password']

    @property
    def connect_to_ssh(self):
        """
        connect_to_ssh permet de créer une socket entre le client et le serveur !
        La connexion restera active tant que l'instance sera existante !
        """
        return self.instance.connect(
            hostname=self.credentials[0],
            port=self.credentials[1],
            username=self.credentials[2],
            password=self.credentials[3]
        )

    @property
    def add_key(self):
        """
        add_key permet de créer une clé SSH nécessaire au fonctionnement du protocol.
        La clé s'ajoute dans le known_hosts !
        """
        return self.instance.set_missing_host_key_policy(AutoAddPolicy())

    @property
    def close(self):
        """
        close ferme la connexion SSH
        :return:
        """
        return self.instance.close()

    def execute_command(self, command: str):
        """
        Return a string if the instruction return something, else None (executed in the OS stack)
        :return: str
        """
        return self.instance.exec_command(
            command=f"{command}"
        )[1].read().decode('utf-8').splitlines()


def compare_output(output, expected_output):
    if expected_output == "*":
        return True
    if "*" in expected_output:
        return expected_output.replace("*", "") in output
    return output.strip() == expected_output.strip()

def select_points(data: dict):
    choices = {
        "resultats": []
    }
    
    def construct_options(data: dict):
        result = []
        for item in data:
            if item != "description" :
                result.append(f'[{item}] {data[f"{item}"]["description"]}')
        return result
        
    def make_selection(label: str, data: dict):
        return inquirer.Checkbox(
            label,
            message="Sélectionnez les points",
            choices=construct_options(data=data)
        )
    
    def points(result: list, label: str):
        tab = []
        for choice in result[f"{label}"]:
            tab.append(str(choice).split("]")[0][1::].strip())
        return tab
        
    question = [
        make_selection(label='first_choice', data=data)
    ]

    choices['resultats'].append(points(result=inquirer.prompt(question), label="first_choice"))
    return choices['resultats'][0]

# Lancer les vérifications sur les appareils sélectionnés
def run_checks(selected_devices, selected_points, recommendations, username, password):
    total_points = len(selected_points)
    passed_points = 0
    failed_points = []

    def get_node(path):
        keys = path.split('.')
        node = recommendations
        for key in keys:
            node = node.get(key, {})
        return node

    for device in selected_devices:
        ip = device['ip']
        print(f"\nVérification de l'appareil {ip}...")
        for point in selected_points:
            node = get_node(point)
            if 'check_command' in node and 'check_expected_output' in node:
                output = execute_command(ip, username, password, node['check_command'])
                if output is not None:
                    if compare_output(output, node['check_expected_output']):
                        passed_points += 1
                    else:
                        failed_points.append(node['description'])
    
    # Récapitulatif
    print("\nRécapitulatif:")
    print(f"Points vérifiés: {total_points}")
    print(f"Points réussis: {passed_points}")
    print(f"Points échoués: {total_points - passed_points}")
    print("\nPoints échoués:")
    for point in failed_points:
        print(f"X {point}")

def replace_set_command(data):
    if isinstance(data, dict):
        keys_to_replace = []
        for key, value in data.items():
            if isinstance(value, dict):
                data[key] = replace_set_command(value)
                if 'check_expected_output' in value:
                    keys_to_replace.append(key)
            elif isinstance(value, list):
                data[key] = [replace_set_command(item) for item in value if isinstance(item, dict)]
            else:
                if key == "set_command":
                    keys_to_replace.append(key)
        
        for key in keys_to_replace:
            if key == "set_command":
                data[key] = {"end": True}
    
    elif isinstance(data, list):
        for i in range(len(data)):
            data[i] = replace_set_command(data[i])
    
    return data


def result_add(result_selection: list):
    for element in result_selection:
        globals()["result"].append(element)

def get_level_dict(data, level):
    keys = level
    current_dict = data
    
    for key in keys:
        if key in current_dict:
            current_dict = current_dict[key]
        else:
            return None  # Le niveau demandé n'existe pas
    
    return current_dict


def recursive_traversal(json_data):
    from collections import deque

    queue = deque([json_data])  # Utilisation d'une file d'attente (FIFO)

    while queue:
        current_data = queue.popleft()

        # Sélection des points à partir des données actuelles
        try:
            selected_indices = select_points(current_data)
        except Exception as e:
            continue

        if not selected_indices:
            continue

        # Traitement des données sélectionnées
        result_add(result_selection=selected_indices)

        # Vérification si les enfants doivent être ajoutés à la file d'attente
        for index in selected_indices:
            if index in current_data and isinstance(current_data[index], dict):
                queue.append(current_data[index])

def level_to_list(level: str) -> list:
    tab = []
    

def numeric_sort_key(value):
    # Diviser la chaîne par les points et convertir les parties en entiers
    parts = split(r'\.', value)
    return [int(part) for part in parts]

def level_to_list(level: str) -> list:
    tab = []
    last_lvl = ""
    for [index, chiffre] in enumerate(level.split(".")):
        if index == 0:
            tab.append(chiffre)
            last_lvl = chiffre
        else:
            last_lvl = f"{last_lvl}.{chiffre}"
            tab.append(last_lvl)
    return tab


def get_dict_level(data: dict, level: str) -> None or dict:
    res = None
    new_data = data
    for level in level_to_list(level=level):
        new_data = new_data[level]
        res = new_data
    return res

def main():
    devices = load_devices('closest_version.csv')
    selected_devices = select_devices(devices)
    username, password = get_credentials()
    
    globals()["result"] = []

    data = replace_set_command(data=Recommendation().read_file())
    temp_data = data

    recursive_traversal(json_data=temp_data)
    globals()["result"] = sorted(globals()["result"], key=numeric_sort_key)
    
    for index in globals()["result"]:
        r = get_dict_level(data=data, level=index)
        if "check_command" in r:
            check_cmd = r["check_command"]

    #run_checks(selected_devices, selected_points, recommendations, username, password)

if __name__ == "__main__":
    main()
