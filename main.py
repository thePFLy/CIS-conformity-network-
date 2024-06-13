from modules.ssh_class import SSH
from modules.env_class import SecretEnv
from modules.recommendations_class import Recommendation
from modules.interactivity_class import Selection
from modules.scan_class import CiscoScanner
from modules.json_class import JsonData
from modules.scores import Score
from rich.console import Console
from rich.panel import Panel
from os import system as sys
from platform import system as p_sys
from argparse import ArgumentParser
from re import findall
from json import dumps
from fastapi import FastAPI



app = FastAPI()

# Chargement du module de gestion des ENV
env = SecretEnv()
json = JsonData()
scan = CiscoScanner()


@app.get(
    path="/get_devices",
)
async def get_devices():
    return json.content["devices"]


"""
Points futurs à déployer:
- Mise en place d'une API avec FastAPI pour manipuler CIS via une page web ou des ressources externes (api ouverte)
- 
"""

def print(content: str, title: str = None, width: int = 1200, clear: bool = False, color: str = "green"):
    if clear:
        if p_sys() == "Windows":
            sys("cls")
        else:
            sys("clear")

    panel_1 = Panel.fit(f"{content}", title=title, width=width, title_align="left", style=color, padding=1)
    Console(record=True).print(panel_1)

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

def get_dict_level(data: dict, level: str):
    res = None
    new_data = data
    for level in level_to_list(level=level):
        new_data = new_data[level]
        res = new_data
    return res

def remake_tab(rec_tab: list, version: str):
    new_tab = []
    for point in rec_tab:
        new_dict = get_dict_level(data=Recommendation(filename=version).read_file(), level=point)
        for sub_point in new_dict:
            if isinstance(new_dict[sub_point], dict) and sub_point != "description" and "check_command" in new_dict[sub_point]:
                if "required" in new_dict:
                    print(
                        title="Choix facultatif...",
                        content=f"Point: {sub_point}\nDescription: {get_dict_level(data=Recommendation(filename=version).read_file(), level=point)['description']}\n\nIl s'agit d'un point non obligatoire, voulez-vous le tester ?",
                        color="yellow"
                    )
                    choice = input("Votre choix (O/N) > ").capitalize().strip()
                    if choice == "O":
                        new_tab.append(sub_point)
                    else:
                        new_tab.append(sub_point)
                else:
                    new_tab.append(sub_point)
    return new_tab

def complete_command(template):
    placeholders = findall(r'<(.*?)>|\{(.*?)\}', template)
    values = []

    for placeholder in placeholders:
        if placeholder[0]:
            question = f"Entrez la valeur pour '{placeholder[0].replace('|', 'ou')}': "
        else:
            question = f"Entrez la valeur pour '{placeholder[1].replace('|', 'ou' )}': "
        value = input(question)
        values.append(value)

    completed_string = template
    for placeholder, value in zip(placeholders, values):
        completed_string = completed_string.replace('<' + placeholder[0] + '>', value)
        completed_string = completed_string.replace('{' + placeholder[1] + '}', value)

    return completed_string

def is_no_mode(output: str):
    return output.startswith("no") or output.startswith("*no")

def is_expected_output(output, expected_output):
    if expected_output.startswith("*") and expected_output.endswith("*") and is_no_mode(output=output) and is_no_mode(output=expected_output):
        return expected_output[1:-1] in output
    elif expected_output.startswith("*") and is_no_mode(output=output) and is_no_mode(output=expected_output):
        return output.endswith(expected_output[1:])
    elif expected_output.endswith("*"):
        return output.startswith(expected_output[:-1])
    else:
        return output == expected_output

if __name__ == "__main__":
    args = ArgumentParser()
    args.add_argument("-s", "--scan", action='store_true')
    args.add_argument("-dd", "--delete-device", action='store_true')
    args.add_argument("-d", "--device")
    args = args.parse_args()

    if args.delete_device:
        if args.device is None:
            print(
                title="Erreur !",
                content="Vous devez donner une valeur à device via --device [name]",
                color="red"
            )
            exit()
        if args.device not in json.content["devices"]:
            print(
                title="Erreur !",
                content=f"{args.device} n'existe pas dans votre configuration !",
                color="red"
            )
            exit()
        json.delete_device(key=args.device)
        env.delete_device(device=args.device)
        print(title="Résultat", content=f"Confirmation de la suppression de {args.device}", clear=True)
        exit()
    if args.scan:
        finded_devices = []

        for network_address in json.content["networks_ip"]:
            print(
                title="Scan...",
                content=f"Scan du réseau {network_address} en cours...\nVeuillez patienter avant de choisir les IP a tester.",
                clear=True
            )
            finded_devices.append(
                Selection(
                    data=scan.scan_network(
                        network=network_address
                    ),
                    label="ip_find",
                    device_selection=True
                ).results["resultats"]
            )

        finded_devices = [item for sublist in finded_devices for item in sublist]
        new_json = json.read_json()

        # Encoder les données des nouveaux devices !
        for device in finded_devices:
            reconfigure = False
            if json.device_exist(ip=device):
                print(
                    title="Choix de configuration:",
                    content=f"Il existe déjà une configuration pour la machine {device}",
                    clear=True
                )
                reconfigure = input("La reconfigurer ? (O/N): ").capitalize().strip()
            if not json.device_exist(ip=device) or reconfigure == "O":
                if reconfigure == "O":
                    json.delete_device(key=json.get_hostname(ip=device))
                    env.delete_device(device=json.get_hostname(ip=device))
                print(
                    title="Configuration:",
                    content=f"Configuration pour l'IP {device}",
                    clear=True
                )
                hostname = input("hostname > ")
                new_json["devices"][hostname] = {}
                new_json["devices"][hostname]["username"] = input("username > ")
                new_json["devices"][hostname]["ip"] = device
                new_json["devices"][hostname]["port"] = input("port > ")
                env.set(device=hostname, password=input("password > "), secret=input("secret > "))
                ver = scan.get_device_model_and_ios_version(ip=device)
                new_json["devices"][hostname]["version"] = scan.find_closest_version(ios_version=ver)
                json.set(new_dict=new_json)
    
    if len(json.read_json()["devices"]) == 0:
        print(
            title="Aucun appareil à tester !",
            content="Il n'y aucun appareil que vous n'ayez reglé\nUtilisez -s ou --scan pour en encoder des nouveaux.",
            color="red",
            clear=True
            )
        exit()

    # Pour récuperer les choix, utiliser <variable>.results (et <variable>.results["resultats"] pour obtenir directement la liste)
    print(
        title=f"Choix des appareils",
        content=f"Veuillez choisir quels appareils vous souhaitez tester.",
        clear=True
    )
    device_select = Selection(data=json.read_json()["devices"], label="choix_device", device_selection=True)

    scores = {}

    for device in device_select.results["resultats"]:
        print(
            title=f"Choix de score pour {device}",
            content=f"Veuillez choisir quel points vous souhaitez tester.",
            clear=True
        )
        rec = Selection(
            data=Recommendation(filename=json.get(device=device, key="version")).read_file(),
            label="choix_points",
            device_selection=False,  
            auto_sort=True
        )

        print(
            title=f"Tentative de connexion à {device}", 
            content=f"Vérification de l'appareil {device} V.{json.get(device=device, key='version')}... ",
            clear=True
        )
        socket = SSH(
            ip=json.get(device=device, key='ip'),
            port=json.get(device=device, key='port'),
            username=json.get(device=device, key='username'),
            password=env.get(device=device, pass_type="PWD"),
            secret=env.get(device=device, pass_type="SEC"),
            version=json.get(device=device, key='version')
        )
        socket.connect_to_ssh()

        rec.results["resultats"] = remake_tab(rec_tab=rec.results["resultats"], version=json.get(device=device, key="version"))
        score = Score(result_list=rec.results["resultats"])


        recc = Recommendation(filename=json.get(device=device, key="version"))
        inc_win = 0
        inc_fail = 0
        max_inc = len(rec.results["resultats"])
        for [index, point] in enumerate(rec.results["resultats"], start=1):
            description = get_dict_level(data=recc.read_file(), level=point)["description"]
            expec_cmd = get_dict_level(data=recc.read_file(), level=point)["check_expected_output"]
            check_cmd = get_dict_level(data=recc.read_file(), level=point)["check_command"]
            execution = socket.execute_command(command=check_cmd)
            comparaison = is_expected_output(output=execution, expected_output=complete_command(template=expec_cmd))
            if comparaison:
                inc_win += 1
            else:
                inc_fail += 1
            print(
                title="Progression du scan...", 
                content=f"Test en cours: {description}\n\n{index} tests sur {max_inc} passés...\nTests réussis: {inc_win}\nTests échoués: {inc_fail}", 
                clear=True,
                color="blue"
            )
            score.result(
                n_test=point,
                is_success=comparaison,
                description=get_dict_level(
                    data=recc.read_file(), 
                    level=point
                )["description"],
                get_result=execution
            )
        scores[device] = score
        with open(file=f"rapport/{device}.txt", mode="w", encoding="utf-8") as rapport:
            rapport.write(dumps(scores[device].results, indent=4))
    """
    print(
        title="Résultat des tests",
        content=f"Toutes les tests on été passés !",
        clear=True
    )
    """
