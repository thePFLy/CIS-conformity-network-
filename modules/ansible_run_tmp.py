import ansible_runner
import os
import yaml

# Chemin vers le fichier d'inventaire
INVENTORY_FILE = '/etc/ansible/hosts'

def get_hosts_from_inventory():
    """Obtenir les hôtes de l'inventaire Ansible."""
    import ansible.inventory.manager
    import ansible.parsing.dataloader

    loader = ansible.parsing.dataloader.DataLoader()
    inventory = ansible.inventory.manager.InventoryManager(loader=loader, sources=[INVENTORY_FILE])
    hosts = inventory.get_hosts()
    return {host.name: host.vars.get('ansible_host', host.name) for host in hosts}

def flatten_list(nested_list):
    """Aplatir une liste de listes en une seule liste."""
    return [item for sublist in nested_list for item in sublist]

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

def process_results(results):
    """Afficher les résultats de l'exécution du playbook."""
    print("Standard Output:")
    print(results['stdout'])
    print("\nStandard Error:")
    print(results['stderr'])

def main():
    hosts = get_hosts_from_inventory()
    print("Appareils disponibles :")
    for i, (name, ip) in enumerate(hosts.items(), start=1):
        print(f"{i}. {name} ({ip})")

    choice = int(input("Sélectionnez un appareil (numéro) : ")) - 1
    selected_ip = list(hosts.values())[choice]

    commands = [
        "show ip route"
    ]

    results = run_ansible_commands(selected_ip, commands)
    process_results(results)

if __name__ == "__main__":
    main()
