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
from smtplib import SMTP
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


arg = ArgumentParser()
arg.add_argument("-d", "--daemon", action="store_true", help="Run as daemon")
arg.add_argument("-n", "--now", action="store_true", help="Run as now")
arg.add_argument("-sv", "--set-value", action="store_true", help="Run as set value")
arg = arg.parse_args()

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

def stock_default_value(ip: str, level: str, type_command: str, key: str, default_value: str):
    if not exists(rf"ressources/default_values/{ip}.json"):
        with open(rf"ressources/default_values/{ip}.json", "r") as file:
            file.write(dumps({}, indent=2))
    else:
        with open(rf"ressources/default_values/{ip}.json", "r") as file:
            data = load(file)
        if not level in data:
            data[level] = {}
        if not type_command in data[level]:
            data[level][type_command] = {}
        data[level][type_command][key] = default_value

        with open(rf"ressources/default_values/{ip}.json", "w") as file:
            file.write(dumps(data, indent=2))

def complete_command(template, ip: str, level: str, type_value: str, set_mode: bool):
    placeholders = findall(r'<(.*?)>|\{(.*?)\}', template)
    values = []

    for placeholder in placeholders:
        if placeholder[0]:
            question = f"[{type_value}] Entrez la valeur pour '{placeholder[0].replace('|', 'ou')}': "
            key = placeholder[0].replace("|", "ou")
        else:
            question = f"[{type_value}] Entrez la valeur pour '{placeholder[1].replace('|', 'ou')}': "
            key = placeholder[1].replace("|", "ou")
        value = input(question)
        if set_mode:
            stock_default_value(ip=ip, level=level, type_command=type_value, key=key, default_value=value)
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

def send_mail(body_text: str):
    with open(file="ressources/config.ini", mode="r") as file:
        data = file.readlines()
    data_dict = {}
    for line in data:
        data_dict[line.split("=")[0].strip()] = line.split("=")[1].strip()
    msg = MIMEMultipart()
    msg["From"] = data_dict["MAIL_SENDER"]
    msg["To"] = data_dict["MAIL_RECIPIENT"]
    msg["Subject"] = "Rapport d'erreur !"
    msg.attach(MIMEText(body_text, "plain"))

    try:
        server = SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(user=data_dict["MAIL_SENDER"], password=data_dict["PASSWORD"])
        text = msg.as_string()
        server.sendmail(data_dict["MAIL_SENDER"], data_dict["MAIL_RECIPIENT"], text)
    except Exception as e:
        print(e)
    finally:
        server.quit()




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
                set_cmd = get_dict_level(data=recc.read_file(), level=point)["set_command"]
                expec_cmd = get_dict_level(data=recc.read_file(), level=point)["check_expected_output"]
                check_cmd = get_dict_level(data=recc.read_file(), level=point)["check_command"]
                check_cmd = complete_command(template=check_cmd, ip=device["ip"], level=point, type_value="check_command", set_mode=arg.set_value)
                set_cmd = complete_command(template=set_cmd, ip=device["ip"], level=point, type_value="set_command", set_mode=arg.set_value)
                try:
                    level = get_dict_level(data=recc.read_file(), level=point)["level"]
                except:
                    level = None
                got_answer = run_com(socket=ssh, command=check_cmd)
                awaited_answer = complete_command(template=expec_cmd, ip=device["ip"], level=point, type_value="expected", set_mode=arg.set_value)
                comparaison = is_expected_output(output=got_answer, expected_output=awaited_answer)
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
                    get_result=got_answer,
                    expected=expec_cmd,
                    command=check_cmd,
                    ip=device["ip"],
                    level=level
                )
            ssh.close()
            send_mail(body_text=score.save())

    elif arg.daemon:
        """
        Reaction Auto
        """
        with open(file=rf"ressources/default_values/hosts.json", mode="r", encoding="utf-8") as f:
            data = load(f)["to_scan"]
        for ip in data:
            print(ip)
    else:
        print("Nothing happen...")
