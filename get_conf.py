import csv
import getpass
from netmiko import ConnectHandler, NetmikoAuthenticationException, NetmikoTimeoutException
import inquirer

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

def show_running_config(ip, username, password):
    device = {
        'device_type': 'cisco_ios',
        'ip': ip,
        'username': username,
        'password': password,
        'secret': 'cisco'
    }
    try:
        connection = ConnectHandler(**device)
        connection.enable()
        output = connection.send_command('show running-config')
        print(f"Configuration de l'appareil {ip}:\n{output}")
        connection.disconnect()
        return output
    except NetmikoAuthenticationException:
        print(f"Échec de l'authentification pour l'appareil {ip}.")
    except NetmikoTimeoutException:
        print(f"L'appareil {ip} n'est pas accessible via SSH.")
    except Exception as e:
        print(f"Erreur lors de la connexion à l'appareil {ip}: {e}")

def save_config(ip, version, config):
    filename = f"{ip}_{version.replace(' ', '_')}.txt"
    with open(filename, 'w') as file:
        file.write(config)
    print(f"Configuration sauvegardée dans {filename}")

def main():
    devices = load_devices('closest_version.csv')
    selected_devices = select_devices(devices)
    username, password = get_credentials()
    for device in selected_devices:
        ip = device['ip']
        version = device['version']
        print(f"L'appareil avec IP {ip} et version {version} a été sélectionné.")
        config = show_running_config(ip, username, password)
        if config:
            save_config(ip, version, config)

if __name__ == "__main__":
    main()
