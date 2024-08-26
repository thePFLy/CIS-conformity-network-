from modules.ansible_config import AnsibleConfig
from modules.recommendations_class import Recommendation
from modules.interactivity_class import Selection
from modules.ssh_class import SSH
from modules.scores import Score
from rich.console import Console
from rich.panel import Panel
from os import system as sys
from platform import system as p_sys
from re import findall
from json import dumps
import tempfile
import yaml
import ansible_runner


# Chargement du module de gestion des ENV
ans_conf = AnsibleConfig()

def run_com(socket: object, command: str):
    return socket.execute_command(command=command)


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


def remake_tab(rec_tab: list):
    new_tab = []
    for point in rec_tab:
        new_dict = get_dict_level(data=Recommendation().read_file(), level=point)
        for sub_point in new_dict:
            if isinstance(new_dict[sub_point], dict) and sub_point != "description" and "check_command" in new_dict[
                sub_point]:
                if "required" in new_dict:
                    print(
                        title="Choix facultatif...",
                        content=f"Point: {sub_point}\nDescription: {get_dict_level(data=Recommendation().read_file(), level=point)['description']}\n\nIl s'agit d'un point non obligatoire, voulez-vous le tester ?",
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
            question = f"Entrez la valeur pour '{placeholder[1].replace('|', 'ou')}': "
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
    if expected_output.startswith("*") and expected_output.endswith("*") and is_no_mode(output=output) and is_no_mode(
            output=expected_output):
        return expected_output[1:-1] in output
    elif expected_output.startswith("*") and is_no_mode(output=output) and is_no_mode(output=expected_output):
        return output.endswith(expected_output[1:])
    elif expected_output.endswith("*"):
        return output.startswith(expected_output[:-1])
    else:
        return output == expected_output

def run_ansible_commands(selected_ip, commands):
    """Exécuter des commandes sur un hôte en utilisant Ansible Runner."""
    playbook = [{
        'hosts': selected_ip,
        'gather_facts': 'no',
        'tasks': [
            {'name': f'Run command: {cmd}', 'ios_command': {'commands': [cmd]}} for cmd in commands
        ]
    }]

    # Créer un répertoire temporaire pour les fichiers de données
    with tempfile.TemporaryDirectory() as temp_dir:
        # Sauvegarder le playbook temporairement
        playbook_path = os.path.join(temp_dir, 'playbook.yml')
        with open(playbook_path, 'w') as f:
            yaml.dump(playbook, f)

        # Exécuter le playbook via ansible_runner
        r = ansible_runner.run(
            private_data_dir=temp_dir,
            playbook=playbook_path,
            inventory=INVENTORY_FILE
        )

        stdout = []
        stderr = []

        # Traiter les événements pour capturer le stdout et stderr
        for event in r.events:
            if 'event_data' in event and 'res' in event['event_data']:
                res = event['event_data']['res']
                if 'stdout' in res:
                    stdout.append(res['stdout'])
                if 'stderr' in res:
                    stderr.append(res['stderr'])

        # Aplatir les listes et joindre les résultats
        stdout = flatten_list(stdout)
        stderr = flatten_list(stderr)

        results = {
            'stdout': "\n".join(stdout) if stdout else 'No stdout',
            'stderr': "\n".join(stderr) if stderr else 'No stderr'
        }

        return results

if __name__ == "__main__":
    # Pour récuperer les choix, utiliser <variable>.results (et <variable>.results["resultats"] pour obtenir directement la liste)
    print(
        title=f"Choix des appareils",
        content=f"Veuillez choisir quels appareils vous souhaitez tester.",
        clear=True
    )
    device_select = Selection(data=ans_conf.data, label="choix_device", device_selection=True)

    scores = {}

    for device in device_select.results["resultats"]:
        print(
            title=f"Choix de score pour {device['ip']} | MODE: {device['device_type']}",
            content=f"Veuillez choisir quel points vous souhaitez tester.",
            clear=True
        )
        rec = Selection(
            data=Recommendation().read_file(),
            label="choix_points",
            device_selection=False,
            auto_sort=True
        )
        print(
            title=f"Tentative de connexion à {device['ip']} | MODE: {device['device_type']}",
            content=f"Vérification de l'appareil {device['ip']}... ",
            clear=True
        )

        rec.results["resultats"] = remake_tab(rec_tab=rec.results["resultats"],)

        score = Score(result_list=rec.results["resultats"])

        recc = Recommendation()
        inc_win = 0
        inc_fail = 0
        max_inc = len(rec.results["resultats"])
        device_vars = ans_conf.get_devices_vars(device=device["device_type"])
        print(dumps(device_vars, indent=2))
        ssh = SSH(
            ip=device["ip"],
            username=device_vars["ansible_user"],
            password=device_vars["ansible_password"],
            port=device_vars["ansible_port"],
            secret=device_vars["ansible_become_pass"]
        )
        ssh.connect_to_ssh()

        for [index, point] in enumerate(rec.results["resultats"], start=1):
            description = get_dict_level(data=recc.read_file(), level=point)["description"]
            expec_cmd = get_dict_level(data=recc.read_file(), level=point)["check_expected_output"]
            check_cmd = get_dict_level(data=recc.read_file(), level=point)["check_command"]
            execution = run_com(socket=ssh, command=check_cmd)
            comparaison = is_expected_output(output=execution, expected_output=complete_command(template=expec_cmd))
            if comparaison:
                inc_win += 1
            else:
                inc_fail += 1
            print(
                title="Progression du scan...",
                content=f"Test en cours: {description}\n\n{index} tests sur {max_inc} passés...\nTests réussis: {inc_win}\nTests échoués: {inc_fail}",
                clear=True,
                color="cyan"
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
        ssh.close()
        scores[device] = score
        with open(file=f"rapport/{device}.txt", mode="w", encoding="utf-8") as rapport:
            rapport.write(dumps(scores[device].results, indent=4))
