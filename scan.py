import nmap
from pysnmp.hlapi import *
import re
import csv
from fuzzywuzzy import fuzz
import argparse

def scan_network(network):
    nm = nmap.PortScanner()
    nm.scan(hosts=network, arguments='-sn')

    devices = []
    for ip in nm.all_hosts():
        devices.append(ip)

    return devices

def get_device_type(model):
    match = re.search(r'Cisco\s+(.*?)\s+Software', model)
    if match:
        return match.group(1)
    return None

def get_device_model_and_ios_version(ip, community='public'):
    try:
        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(),
                   CommunityData(community),
                   UdpTransportTarget((ip, 161)),
                   ContextData(),
                   ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysDescr', 0)))
        )

        if errorIndication:
            print(f'Error: {errorIndication}')
            return None, None, None

        model = varBinds[0][1].prettyPrint()

        # Extracting iOS version from sysDescr
        # Extracting device type
        device_type = get_device_type(model)
        ios_version = None
        match = re.search(r'Version (\d+\.\d+)', model)
        if match:
            ios_version = f"Cisco {device_type} {match.group(1)}"

        return model, ios_version, device_type if device_type else "Unknown"
    except Exception as e:
        print(f"Error while querying {ip}: {e}")
        return None, None, None

def get_device_hostname(ip, community='public'):
    try:
        errorIndication, errorStatus, errorIndex, varBinds = next(
            getCmd(SnmpEngine(),
                   CommunityData(community),
                   UdpTransportTarget((ip, 161)),
                   ContextData(),
                   ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysName', 0)))
        )

        if errorIndication:
            print(f'Error: {errorIndication}')
            return None

        hostname = varBinds[0][1].prettyPrint()
        return hostname
    except Exception as e:
        print(f"Error while querying {ip} for hostname: {e}")
        return None

def load_cisco_versions(filename):
    versions = []
    with open(filename, newline='') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if row:
                versions.append(row[0])
    return versions

def find_closest_version(ios_version, cisco_versions):
    closest_match = None
    highest_ratio = 0

    for version in cisco_versions:
        ratio = fuzz.ratio(ios_version, version)
        if ratio > highest_ratio:
            highest_ratio = ratio
            closest_match = version

    return closest_match

def save_closest_version(ip, name, ios_version, filename):
    if ios_version:
        # Vérifier si la ligne existe déjà dans le fichier CSV
        with open(filename, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row[0] == ip and row[1] == name and row[2] == ios_version:
                    return  # Quitter la fonction si la ligne existe déjà

        # Ajouter la nouvelle ligne dans le fichier CSV
        with open(filename, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([ip, name, ios_version])

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Scan a network for devices and retrieve Cisco device information.')
    parser.add_argument('network', help='The network range to scan (e.g., 10.10.10.0/24)')
    args = parser.parse_args()

    network = args.network
    devices = scan_network(network)

    cisco_versions = load_cisco_versions('cisco_versions.csv')

    for ip in devices:  
        model, ios_version, device_type = get_device_model_and_ios_version(ip)
        name = get_device_hostname(ip)
        print(f"IP: {ip}, Name: {name}, Model: {model}, iOS Version: {ios_version}, Device Type: {device_type}")
        save_closest_version(ip, name, ios_version, "closest_version.csv")
