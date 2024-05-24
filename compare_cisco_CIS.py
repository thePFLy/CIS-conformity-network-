import json
import csv
import getpass
from netmiko import ConnectHandler, NetmikoAuthenticationException, NetmikoTimeoutException
import inquirer

# Charger le fichier JSON de recommandations
def load_recommendations(json_file):
    with open(json_file, 'r') as file:
        return json.load(file)

# Charger les appareils à partir du fichier CSV
def load_devices(filename):
    devices = []
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            devices.append({'ip': row[0], 'version': row[1]})
    return devices

# Sélectionner les appareils à sécuriser
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

# Obtenir les identifiants de l'utilisateur
def get_credentials():
    username = input("Entrez votre nom d'utilisateur: ")
    password = getpass.getpass(prompt="Entrez votre mot de passe: ")
    return username, password

# Exécuter une commande sur un appareil Cisco et retourner la sortie
def execute_command(ip, username, password, command):
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
        output = connection.send_command(command)
        connection.disconnect()
        return output
    except (NetmikoAuthenticationException, NetmikoTimeoutException, Exception) as e:
        print(f"Erreur lors de la connexion à l'appareil {ip}: {e}")
        return None

# Comparer la sortie d'une commande avec le résultat attendu
def compare_output(output, expected_output):
    if expected_output == "*":
        return True
    if "*" in expected_output:
        return expected_output.replace("*", "") in output
    return output.strip() == expected_output.strip()

# Sélectionner les points à vérifier
def select_points(recommendations):
    def traverse(node, path=""):
        points = {}
        if 'description' in node and list(node.keys()) == ["description"]:
            points[path.strip(".")] = node['description']
        for key, value in node.items():
            if isinstance(value, dict):
                points.update(traverse(value, path + key + "."))
                print(points)
        return points

    all_points = traverse(recommendations)
    questions = [
        inquirer.Checkbox('selected_points',
                          message="Sélectionnez les points de contrôle à vérifier",
                          choices=[f"{key} {value}" for key, value in all_points.items()])
    ]
    answers = inquirer.prompt(questions)
    selected_keys = [item.split(" ")[0] for item in answers['selected_points']]
    return selected_keys

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

def main():
    json_file = 'recommendations.json'  # Remplacez par le nom de votre fichier JSON
    recommendations = load_recommendations(json_file)
    devices = load_devices('closest_version.csv')
    selected_devices = select_devices(devices)
    username, password = get_credentials()
    selected_points = select_points(recommendations)
    run_checks(selected_devices, selected_points, recommendations, username, password)

if __name__ == "__main__":
    main()
