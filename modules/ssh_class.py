from netmiko import ConnectHandler, NetmikoAuthenticationException, NetmikoTimeoutException



class SSH:
    """
    La classe SSH permet d'instancier une connexion SSH, de s'y connecter
    et d'y exécuter des commandes !
    """
    def __init__(self, ip: str, username: str, password: str, port: int=22, secret: str = None):
        self.creds = {
            "ip": ip,
            "port": int(port),
            "username": username, 
            "password": password,
            "secret": secret,
            "device_type": f"cisco_ios",
            "session_log": "ssh_log.txt"
        }
        self.instance = None

    def connect_to_ssh(self):
        """
        connect_to_ssh permet de créer une socket entre le client et le serveur !
        La connexion restera active tant que l'instance sera existante !
        """
        try:
            self.instance = ConnectHandler(**self.creds)
            self.instance.enable()
            return "réussi"
        except NetmikoAuthenticationException:
            raise NetmikoAuthenticationException(f"Échec de l'authentification pour l'appareil {self.creds['ip']}.")
        except NetmikoTimeoutException:
            raise NetmikoTimeoutException(f"L'appareil {self.creds['ip']} n'est pas accessible via SSH.")
        except Exception as e:
            raise Exception(f"Erreur lors de la connexion à l'appareil {self.creds['ip']}: {e}")


    def close(self):
        """
        close ferme la connexion SSH
        :return:
        """
        return self.instance.disconnect()
    def execute_command(self, command: str):
        """
        Return a string if the instruction return something, else None (executed in the OS stack)
        :return: str
        """
        return self.instance.send_command(f'{command}')