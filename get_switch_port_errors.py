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
import time
from getpass import getpass

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
start_logger = netlib.setup_logging("get_switch_port_errors", output_dir)
logger = start_logger[0]
logger_full_path = start_logger[1]

# instantiate the eAPI library
eapi = netlib.AristaPyeapi(username, password, switch_hostname, logger)

try:
    show_version = eapi.get_version()
    hostname_short = eapi.get_hostname_short()
    print(f"\nHostname: {hostname_short}")
    print(
        f'Model: {show_version["model"]} Hardware Revision: {show_version["hardware_rev"]}'
    )
    print(f'Serial Number: {show_version["serial_number"]}')
    print(f'OS Version: {show_version["eos_version"]}\n')
    port_errors_nz = eapi.try_eapi_command(
        "show interfaces counters errors | nz", "enable", "text"
    )
    print(f"{hostname_short}# show interface counters errors | nz\n")
    print(port_errors_nz)
    print(f"Sleeping for 20 seconds and trying again.")
    time.sleep(20)
    port_errors_nz = eapi.try_eapi_command(
        "show interfaces counters errors | nz", "enable", "text"
    )
    print(f"\n{hostname_short}# show interface counters errors | nz\n")
    print(port_errors_nz)

except KeyboardInterrupt:
    print("Caught Keyboard Interrupt - Exiting the program.")
    sys.exit()

netlib.cleanup_log_if_empty(logger_full_path)
