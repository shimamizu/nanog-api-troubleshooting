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
from getpass import getpass

import netlib

parser = argparse.ArgumentParser()
parser.add_argument(
    "-s",
    "--switch",
    type=str,
    required=True,
    metavar="somehostname.com",
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
start_logger = netlib.setup_logging("get_flash", output_dir)
logger = start_logger[0]
logger_full_path = start_logger[1]

# instantiate the eAPI library
eapi = netlib.AristaPyeapi(username, password, switch_hostname, logger)


def get_storage():
    get_storage = eapi.get_storage()
    print(get_storage)


show_version = eapi.get_version()
version = show_version["eos_version"]
serial_number = show_version["serial_number"]
model = show_version["model"]
hardware_rev = show_version["hardware_rev"]
hostname_short = eapi.get_hostname_short()

print(f"Hostname: {switch_hostname}")
print(f"Model: {model} | Hardware Revision: {hardware_rev}")
print(f"Serial Number: {serial_number}")
print(f"OS Version: {version}")

print(f"\n{hostname_short}# bash timeout 2 sudo df -lh")
get_storage()

netlib.cleanup_log_if_empty(logger_full_path)
