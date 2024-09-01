import configparser
from os import path
from modules.ansible_config import AnsibleConfig
from modules.recommendations_class import Recommendation
from modules.interactivity_class import Selection
from modules.ssh_class import SSH
from modules.scores import Score
from rich.console import Console
from rich.panel import Panel
from os import system as sys
from os.path import exists
from platform import system as p_sys
from re import findall
from argparse import ArgumentParser
from json import load, dumps
from modules.mail_report import SecureEmailSender

arg = ArgumentParser()
arg.add_argument("-d", "--daemon", action="store_true", help="Lance le script sans convoquer de input")
arg.add_argument("-n", "--now", action="store_true", help="Executer maintenant")
arg.add_argument("-sv", "--set-value", action="store_true", help="Si une valeur est mise à jour ou non définie, la stocker de façon permanante")
arg.add_argument("-ar", "--auto-resolve", action="store_true", help="Résoudre automatiquement les tests ratés sans demande de confirmation")
arg.add_argument("-uv", "--update_value", action="store_true", help="Proposer de modifier les valeurs variables si elles sont connues")
arg = arg.parse_args()

# Chargement du module de gestion des ENV
ans_conf = AnsibleConfig()
already_set_vars = {}

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

def stock_default_value(ip: str, level: str, key: str, default_value: str):
    if not exists(rf"ressources/default_values/{ip}.json"):
        with open(rf"ressources/default_values/{ip}.json", "w") as file:
            file.write(dumps({}, indent=2))
    with open(rf"ressources/default_values/{ip}.json", "r") as file:
        data = load(file)
    if not level in data:
        data[level] = {}
    data[level][key] = default_value

    with open(rf"ressources/default_values/{ip}.json", "w") as file:
        file.write(dumps(data, indent=2))

def complete_command(template, ip: str, level: str, set_mode: bool, auto_mod: bool):
    placeholders = findall(r'<(.*?)>|\{(.*?)\}', template)
    values = []
    def value_is_known(ip: str, level: str, key: str, auto_mode: bool):
        if not exists(rf"ressources/default_values/{ip}.json"):
            return False
        with open(file=f"ressources/default_values/{ip}.json", mode="r", encoding="utf-8") as file:
            data = load(file)
        try:
            return data[level][key]
        except:
            if auto_mode:
                raise KeyError(
                    f"La clé {key} pour le point {level} n'a pas été trouvée dans le fichier {ip}.json ou n'as pas de valeurs...")
            else:
                return False

    for placeholder in placeholders:
        if placeholder[0]:
            key = placeholder[0].replace("|", "ou")
            response = value_is_known(ip=ip, level=level, key=key, auto_mode=auto_mod)
            if response:
                if auto_mod or level in already_set_vars and key in already_set_vars[level]:
                    value = response
                else:
                    if arg.update_value:
                        print(
                            title="Valeur existante",
                            content=f"La valeur de {key} est {response}, voulez-vous l'éditer ?",
                            color="red"
                        )
                        if input("Choix o/n: ").capitalize() == "O":
                            question = f"Entrez la valeur pour '{key}': "
                            value = input(question)
                        else:
                            value = response
                    else:
                        value = response
            elif not auto_mod:
                question = f"Entrez la valeur pour '{key}': "
                value = input(question)
            else:
                raise KeyError(
                    f"La clé {key} pour le point {level} n'a pas été trouvée dans le fichier {ip}.json ou n'as pas de valeurs...")
        else:
            key = placeholder[1].replace("|", "ou")
            response = value_is_known(ip=ip, level=level, key=key, auto_mode=auto_mod)
            if response:
                if auto_mod or level in already_set_vars and key in already_set_vars[level]:
                    value = response
                else:
                    if arg.update_value:
                        print(
                            title="Valeur existante",
                            content=f"La valeur de {key} est {response}, voulez-vous l'éditer ?",
                            color="red"
                        )
                        if input("Choix o/n: ").capitalize() == "O":
                            question = f"Entrez la valeur pour '{key}': "
                            value = input(question)
                        else:
                            value = response
                    else:
                        value = response
            elif not auto_mod:
                question = f"Entrez la valeur pour '{key}': "
                value = input(question)
            else:
                raise KeyError(
                    f"La clé {key} pour le point {level} n'a pas été trouvée dans le fichier {ip}.json ou n'as pas de valeurs...")

        if set_mode:
            stock_default_value(ip=ip, level=level, key=key, default_value=value)
            if level not in already_set_vars:
                already_set_vars[level] = None
            already_set_vars[level] = key
        values.append(value)

    completed_string = template
    for placeholder, value in zip(placeholders, values):
        completed_string = completed_string.replace('<' + placeholder[0] + '>', value)
        completed_string = completed_string.replace('{' + placeholder[1] + '}', value)

    return completed_string


def is_no_mode(output: str):
    return output.startswith("no") or output.startswith("no")

def is_expected_output(output, expected_output):
    if expected_output.startswith("*") and expected_output.endswith("*"):
        return expected_output[1:-1] in output
    elif expected_output.startswith("*"):
        return output.endswith(expected_output[1:])
    elif expected_output.endswith("*"):
        return output.startswith(expected_output[:-1])
    else:
        return output == expected_output

def try_resolve_line(ip: str, level: str):
    content = get_dict_level(data=Recommendation().read_file(), level=level)
    if "set_command" in content:
        command = complete_command(template=content["set_command"], ip=ip, level=level, set_mode=False, auto_mod=True)
        text = ""
        if arg.auto_resolve:
            text = "\n- La commande de résolution a été executée..."
        print(
            title="Possibilité de résolution d'erreur !",
            content=f"Nous avons trouvé une instruction pour résoudre l'erreur du cas {level}\n"
                    f"- Description: {content['description']}\n"
                    f"- Commande: {command}\n"
                    f"- AutoResolve: {'Activé' if arg.auto_resolve else 'Désactivé'}{text}",
            color="red"
        )
        if arg.auto_resolve:
            return command


if __name__ == "__main__":
    if arg.now:
        """
        Séléction des devices à tester...
        Pour récuperer les choix, utiliser <variable>.results (et <variable>.results["resultats"] pour obtenir directement la liste)
        """
        print(
            title=f"Choix des appareils",
            content=f"Veuillez choisir quels appareils vous souhaitez tester.",
            clear=True
        )
        device_select = Selection(data=ans_conf.data, label="choix_device", device_selection=True)

        """
        Gestion des scores...
        """
        scores = {}

        for device in device_select.results["resultats"]:
            """
            Sélection des devices à tester...
            """
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
                print(
                    title=f"[{point}] Progression du scan...",
                    content=f"Test en cours: {description}\n\n{index} tests sur {max_inc} passés...\nTests réussis: {inc_win}\nTests échoués: {inc_fail}",
                    clear=True,
                    color="cyan"
                )
                set_cmd = get_dict_level(data=recc.read_file(), level=point)["set_command"]
                expec_cmd = get_dict_level(data=recc.read_file(), level=point)["check_expected_output"]
                check_cmd = get_dict_level(data=recc.read_file(), level=point)["check_command"]
                check_cmd = complete_command(template=check_cmd, ip=device["ip"], level=point, set_mode=arg.set_value, auto_mod=False)
                set_cmd = complete_command(template=set_cmd, ip=device["ip"], level=point, set_mode=arg.set_value, auto_mod=False)
                try:
                    level = get_dict_level(data=recc.read_file(), level=point)["level"]
                except:
                    level = None
                got_answer = run_com(socket=ssh, command=check_cmd)
                awaited_answer = complete_command(template=expec_cmd, ip=device["ip"], level=point, set_mode=arg.set_value, auto_mod=False)
                comparaison = is_expected_output(output=got_answer, expected_output=awaited_answer)
                if comparaison:
                    inc_win += 1
                else:
                    inc_fail += 1
                score.result(
                    n_test=point,
                    is_success=comparaison,
                    description=get_dict_level(
                        data=recc.read_file(),
                        level=point
                    )["description"],
                    get_result=got_answer,
                    expected=expec_cmd,
                    command=check_cmd,
                    ip=device["ip"],
                    level=level,
                    solve_command=set_cmd
                )
            for fail in score.results:
                if fail != "title" and not score.results[fail]["result"]:
                        result = try_resolve_line(ip=device["ip"], level=fail)
                        if result is not None:
                            run_com(socket=ssh, command=result)
            score.save()
            ssh.close()

    elif arg.daemon:
        recc = Recommendation()
        score = []
        with open(file=rf"ressources/default_values/hosts.json", mode="r", encoding="utf-8") as f:
            data = load(f)
        """
        Gestion des scores...
        """
        scores = {}

        for ip in data:
            print(
                title=f"Tentative de connexion à {ip} | MODE: {data[ip]['device_type']}",
                content=f"Vérification de l'appareil {ip}... ",
                clear=True
            )

            score = Score(result_list=data[ip]["points"])

            recc = Recommendation()
            inc_win = 0
            inc_fail = 0
            max_inc = len(data[ip]["points"])
            device_vars = ans_conf.get_devices_vars(device=data[ip]['device_type'])
            ssh = SSH(
                ip=ip,
                username=device_vars["ansible_user"],
                password=device_vars["ansible_password"],
                port=device_vars["ansible_port"],
                secret=device_vars["ansible_become_pass"]
            )
            ssh.connect_to_ssh()

            for [index, point] in enumerate(data[ip]["points"], start=1):
                description = get_dict_level(data=recc.read_file(), level=point)["description"]
                print(
                    title=f"[{point}] Progression du scan...",
                    content=f"Test en cours: {description}\n\n{index} tests sur {max_inc} passés...\nTests réussis: {inc_win}\nTests échoués: {inc_fail}",
                    clear=True,
                    color="cyan"
                )
                set_cmd = get_dict_level(data=recc.read_file(), level=point)["set_command"]
                expec_cmd = get_dict_level(data=recc.read_file(), level=point)["check_expected_output"]
                check_cmd = get_dict_level(data=recc.read_file(), level=point)["check_command"]
                check_cmd = complete_command(template=check_cmd, ip=ip, level=point, set_mode=arg.set_value, auto_mod=True)
                set_cmd = complete_command(template=set_cmd, ip=ip, level=point, set_mode=arg.set_value, auto_mod=True)
                try:
                    level = get_dict_level(data=recc.read_file(), level=point)["level"]
                except:
                    level = None
                got_answer = run_com(socket=ssh, command=check_cmd)
                awaited_answer = complete_command(template=expec_cmd, ip=ip, level=point, set_mode=arg.set_value, auto_mod=True)
                comparaison = is_expected_output(output=got_answer, expected_output=awaited_answer)
                if comparaison:
                    inc_win += 1
                else:
                    inc_fail += 1
                score.result(
                    n_test=point,
                    is_success=comparaison,
                    description=get_dict_level(
                        data=recc.read_file(),
                        level=point
                    )["description"],
                    get_result=got_answer,
                    expected=expec_cmd,
                    command=check_cmd,
                    ip=ip,
                    level=level,
                    solve_command=set_cmd
                )
                for fail in score.results:
                    if fail != "title" and not score.results[fail]["result"]:
                        result = try_resolve_line(ip=ip, level=fail)
                        if result is not None:
                            run_com(socket=ssh, command=result)
                score.save()
            ssh.close()


            resolve_file = f'rapport/{ip}.resolve.txt'
            config = configparser.ConfigParser()
            config.read('ressources/config.ini')
            smtp_server = config.get('EMAIL', 'smtp_server').strip()
            smtp_port = config.get('EMAIL', 'smtp_port').strip()
            recipient_email = config.get('EMAIL', 'recipient_email').strip()

            secure_email_sender = SecureEmailSender(smtp_server, smtp_port)
            subject = config.get('EMAIL', 'subject').strip()

            rapport_path = f'rapport/{ip}.txt'
            try:
                with open(rapport_path, 'r', encoding='utf-8') as file:
                    body = file.read()
            except FileNotFoundError:
                print(f"Le fichier {rapport_path} n'a pas été trouvé.")
                body = 'Le fichier demandé est introuvable.'

            if path.exists(resolve_file):
                secure_email_sender.send_email(recipient_email, subject, body, resolve_file)
            else:
                print("resolve.txt n'existe pas. Email non envoyé.")
    else:
        print("Nothing happen...")
