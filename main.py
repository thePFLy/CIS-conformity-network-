from modules.ssh_class import SSH
from modules.env_class import SecretEnv
from modules.recommendations_class import Recommendation
from modules.interactivity_class import Selection
from rich.console import Console
from rich.panel import Panel
from os import system as sys
from platform import system as p_sys


def clear():
    if p_sys() == "Windows":
        sys("cls")
    else:
        sys("clear")

def print(title: str, content: str, width: int = 400):
    panel_1 = Panel.fit(f"{content}", title=title, width=width, title_align="left", style="green", padding=1)
    Console(record=True).print(panel_1)

if __name__ == "__main__":
    # Chargement du module de gestion des ENV
    clear()
    env = SecretEnv()

    # Pour récuperer les choix, utiliser <variable>.results (et <variable>.results["resultats"] pour obtenir directement la liste)
    print(title=f"Choix des appareils", content=f"Veuillez choisir quels appareils vous souhaitez tester !")
    device_select = Selection(data=env.env, label="choix_device", device_selection=True)
    
    for device in device_select.results["resultats"]:
        clear()
        print(title=f"Choix de score pour {device}", content=f"Veuillez choisir quel points vous souhaitez tester !")
        rec = Selection(
            data=Recommendation(filename="recommendations.json").read_file(),
            label="choix_points",
            device_selection=False,  
            auto_sort=True
        )
        clear()
        print(title=f"Tentative de connexion à {device}", content=f"Vérification de l'appareil {device} V.{env.get(name=device, key='VERSION')}... ")
        socket = SSH(
            ip=env.get(name=device, key="IP"),
            port=env.get(name=device, key="PORT"),
            username=env.get(name=device, key="USERNAME"),
            password=env.get(name=device, key="PASSWORD"),
            secret=env.get(name=device, key="SECRET"),
            version=env.get(name=device, key="VERSION")
        )
        socket.connect_to_ssh()
        clear()
        print(title="Resultat", content=rec.results["resultats"], width=400)