from nmap import PortScanner
from pysnmp.hlapi import *
from re import search
from csv import reader as csv_reader, writer as csv_writer
from fuzzywuzzy import fuzz

class CiscoScanner:
    def __init__(self, community: str = 'public'):
        self.community = community
        self.cisco_versions = self.load_cisco_versions(filename="ressources/cisco_versions.csv")

    def scan_network(self, network: str):
        nm = PortScanner()
        nm.scan(hosts=network, arguments='-sn')
        result = {}
        for ip in nm.all_hosts():
            result[ip] = {}
            result[ip]["ip"] = ip
        return result

    def get_device_type(self, model):
        match = search(r'Cisco\s+(.*?)\s+Software', model)
        if match:
            return match.group(1)
        return None

    def get_device_model_and_ios_version(self, ip: str):
        try:
            errorIndication, errorStatus, errorIndex, varBinds = next(
                getCmd(SnmpEngine(),
                       CommunityData(self.community),
                       UdpTransportTarget((ip, 161)),
                       ContextData(),
                       ObjectType(ObjectIdentity('SNMPv2-MIB', 'sysDescr', 0)))
            )

            if errorIndication:
                print(f'Error: {errorIndication}')
                return None, None, None

            model = varBinds[0][1].prettyPrint()
            device_type = self.get_device_type(model=model)
            ios_version = None
            match = search(r'Version (\d+\.\d+)', model)
            if match:
                ios_version = f"Cisco {device_type} {match.group(1)}"

            return ios_version
        except Exception as e:
            print(f"Error while querying {ip}: {e}")
            return None, None, None

    def load_cisco_versions(self, filename):
        self.cisco_versions = []
        with open(filename, newline='') as csvfile:
            csvreader = csv_reader(csvfile)
            self.cisco_versions = [row[0] for row in csvreader if row]
        return self.cisco_versions

    def find_closest_version(self, ios_version):
        closest_match = None
        highest_ratio = 0

        for version in self.cisco_versions:
            ratio = fuzz.ratio(ios_version, version)
            if ratio > highest_ratio:
                highest_ratio = ratio
                closest_match = version

        return closest_match

    def save_closest_version(self, name, ios_version, filename):
        if ios_version:
            with open(filename, 'r') as csvfile:
                csvreader = csv_reader(csvfile)
                for row in csvreader:
                    if row[0] == self.ip and row[1] == name and row[2] == ios_version:
                        return

            with open(filename, 'a', newline='') as csvfile:
                csvwriter = csv_writer(csvfile)
                csvwriter.writerow([self.ip, name, ios_version])
