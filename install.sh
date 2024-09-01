#!/bin/bash

# Maj système
echo "Mise à jour du système..."
sudo apt-get update -y
sudo apt-get upgrade -y

#Python3 & pip
echo "Installation de Python 3 et pip..."
sudo apt-get install -y python3 python3-pip

# Installer les dépendances Python
echo "Installation des dépendances Python..."
pip3 install -r requirements.txt

# Ansible
echo "Installation d'Ansible..."
sudo apt-get install -y ansible

echo "Installation des autres dépendances..."
sudo apt-get install -y openssh-client

# Terminer l'installation
echo "Installation terminée."