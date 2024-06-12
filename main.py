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


def clear():
    if p_sys() == "Windows":
        sys("cls")
    else:
        sys("clear")

def print(content: str, title: str = None, width: int = 400):
    clear()
    panel_1 = Panel.fit(f"{content}", title=title, width=width, title_align="left", style="green", padding=1)
    Console(record=True).print(panel_1)

if __name__ == "__main__":
    args = ArgumentParser()
    args.add_argument("-s", "--scan", action='store_true')
    args.add_argument("-dd", "--delete-device", action='store_true')
    args.add_argument("-d", "--device")
    args = args.parse_args()

    # Chargement du module de gestion des ENV
    clear()
    env = SecretEnv()
    json = JsonData()
    scan = CiscoScanner()
    
    if args.delete_device:
        json.delete_device(key=args.device)
        env.delete_device(device=args.device)
        print(title="Résultat", content=f"Confirmation de la suppression de {args.device}")
        exit()
    if args.scan:
        finded_devices = []

        for network_address in json.content["networks_ip"]:
            print(title="Scan...", content=f"Scan du réseau {network_address} en cours...\nVeuillez patienter avant de choisir les IP a tester !")
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
            if json.device_exist(ip=device):
                print(title="Choix de configuration:", content=f"Il existe déjà une configuration pour la machine {device}")
                reconfigure = input("La reconfigurer ? (O/N): ").capitalize().strip()
            if not json.device_exist(ip=device) or reconfigure == "O":
                print(title="Configuration:", content=f"Configuration pour l'IP {device}")
                hostname = input("hostname > ")
                new_json["devices"][hostname] = {}
                new_json["devices"][hostname]["username"] = input("username > ")
                new_json["devices"][hostname]["ip"] = device
                new_json["devices"][hostname]["port"] = input("port > ")
                env.set(device=hostname, password=input("password > "), secret=input("secret > "))
                new_json["devices"][hostname]
                new_json["devices"][hostname]["version"] = input("username > ")
                json.set(new_dict=new_json)
    
    # Pour récuperer les choix, utiliser <variable>.results (et <variable>.results["resultats"] pour obtenir directement la liste)
    print(title=f"Choix des appareils", content=f"Veuillez choisir quels appareils vous souhaitez tester !")
    device_select = Selection(data=json.read_json()["devices"], label="choix_device", device_selection=True)
    
    scores = {}

    for device in device_select.results["resultats"]:
        print(title=f"Choix de score pour {device}", content=f"Veuillez choisir quel points vous souhaitez tester !")
        rec = Selection(
            data=Recommendation().read_file(),
            label="choix_points",
            device_selection=False,  
            auto_sort=True
        )

        scores[device] = Score(result_list=rec.results["resultats"])

        print(title=f"Tentative de connexion à {device}", content=f"Vérification de l'appareil {device} V.{json.get(device=device, key='version')}... ")
        socket = SSH(
            ip=json.get(device=device, key='ip'),
            port=json.get(device=device, key='port'),
            username=json.get(device=device, key='username'),
            password=env.get(device=device, pass_type="PWD"),
            secret=env.get(device=device, pass_type="SEC"),
            version=json.get(device=device, key='version')
        )
        socket.connect_to_ssh()

    print(title="Résultat de connexion", content=f"Toutes les connexions se sont déroulées avec succès")

