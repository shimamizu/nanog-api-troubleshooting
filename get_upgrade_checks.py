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
import logging
import os
import sys
from datetime import datetime
from getpass import getpass
from pathlib import Path

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
# check for environment variables for TACACS username & password, prompt if missing
username, password = netlib.get_credentials("TACACS")

# open a file for logging errors
start_logger = netlib.setup_logging("get_upgrade_checks", output_dir)
logger = start_logger[0]
logger_full_path = start_logger[1]

# instantiate the eAPI library
eapi = netlib.AristaPyeapi(username, password, switch_hostname, logger)
logs_time_stamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

try:
    switch_hostname_short = eapi.get_hostname_short()
    show_command_array = [
        "show ip route vrf all",
        "show ipv6 route vrf all",
        "show ip route summary",
        "show ipv6 route summary",
        "show ip bgp summary vrf all",
        "show ipv6 bgp summary vrf all",
        "show ip ospf neighbor",
        "show ipv6 ospf neighbor",
        "show ospfv3 neighbor",
        "show interfaces status",
        "show interfaces counters errors",
        "show interfaces counters discards",
        "show interfaces transceiver",
        "show port-channel summary",
        "show lldp neighbors",
        "show mlag detail",
        "show mlag interfaces",
        "show ip arp",
        "show inventory",
        "show version",
        "show extensions",
        "show boot-extensions",
    ]

    show_version = eapi.get_version()
    switch_eos_version = show_version["eos_version"]
    switch_model = show_version["model"]
    if ("DCS-750" in switch_model) or ("DCS-780" in switch_model):
        show_command_array.insert(8, "show module")
    filename = f"{output_dir}/{switch_hostname_short}_{switch_eos_version}_{logs_time_stamp}_upgrade_checks.txt"

    for show_command in show_command_array:
        print(f"Grabbing outputs for [{show_command}]")
        command_output = eapi.try_eapi_command(show_command, "enable", "text")
        with open(filename, "a+") as my_file:
            my_file.write(
                "\n##############################################################\n"
            )
            my_file.write(f"{switch_hostname_short}# {show_command}")
            my_file.write(
                "\n##############################################################\n\n"
            )
            if command_output is None:
                my_file.write("Command returned no data.\n")
            else:
                my_file.write(command_output)
    print(f"Finished outputing all commands to {filename}")

except KeyboardInterrupt:
    print("Caught Keyboard Interrupt - Exiting the program.")
    sys.exit()

netlib.cleanup_log_if_empty(logger_full_path)
