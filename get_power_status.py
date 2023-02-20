#!/usr/bin/env python

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import datetime
import logging
import os
import sys
from getpass import getpass
from subprocess import check_output

from prettytable import PrettyTable

import netlib

parser = argparse.ArgumentParser()
parser.add_argument(
    "-s",
    "--switch",
    type=str,
    required=True,
    metavar="switch.hostname.com",
    help="Hostname of the switch",
)
parser.add_argument(
    "-o",
    "--output_directory",
    type=str,
    required=False,
    default=os.environ.get("HOME", "/tmp"),
    metavar="some_folder",
    help="Folder for all outputs from the script",
)
args = parser.parse_args()
switch_hostname = args.switch
output_dir = args.output_directory
username, password = netlib.get_credentials("TACACS")

# open a file for logging errors
start_logger = netlib.setup_logging("port_data", output_dir)
logger = start_logger[0]
logger_full_path = start_logger[1]

# instantiate the eAPI library
eapi = netlib.AristaPyeapi(username, password, switch_hostname, logger)

show_version = eapi.get_version()
power_status = eapi.try_eapi_command("show environment power", "enable", "text")
power_status_json = eapi.get_power()
get_hostname = eapi.get_hostname_short()
get_power = eapi.get_inventory("power")

if show_version["cli_commands"] == "old":
    location = eapi.try_eapi_command("show snmp location", "enable")["location"]
else:
    location = eapi.try_eapi_command("show snmp v2-mib location", "enable")["location"]

try:
    pdu_table = PrettyTable()
    pdu_table.field_names = ["PSU Number", "PSU Model", "Serial Number"]
    for pdu in get_power:
        pdu_model = get_power[pdu]["name"]
        pdu_serial_number = get_power[pdu]["serialNum"]
        if "PWR" in pdu_model:
            pdu_table.add_row([pdu, pdu_model, pdu_serial_number])
    # uncomment to print the whole table
    # print(pdu_table)
except NameError:
    print("No PDU data found, please investigate.")
print(f"\nHostname: {switch_hostname}")
print(
    f'Model: {show_version["model"]} Hardware Revision: {show_version["hardware_rev"]}'
)
print(f'Serial Number: {show_version["serial_number"]}')
print(f"Location: {location}")
print(f'OS Version: {show_version["eos_version"]}')
for power_supply in power_status_json:
    if power_status_json[power_supply]["state"] != "ok":
        print(
            f'PSU{power_supply} is reporting a state of {power_status_json[power_supply]["state"]} - {get_power[power_supply]["name"]}, SN: {get_power[power_supply]["serialNum"]}'
        )
print(f"\n{get_hostname}# show environment power\n")
print(power_status)

netlib.cleanup_log_if_empty(logger_full_path)
