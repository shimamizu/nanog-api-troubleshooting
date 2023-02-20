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
from pathlib import Path

import pyeapi

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

# retrieve the username and password from environment variables if present
username, password = netlib.get_credentials("TACACS")

# open a file for logging errors
start_logger = netlib.setup_logging("get_flash", output_dir)
logger = start_logger[0]
logger_full_path = start_logger[1]

# instantiate the eAPI library
eapi = netlib.AristaPyeapi(username, password, switch_hostname, logger)

sudo_du = eapi.try_eapi_command(
    "bash timeout 2 sudo du -sch /.overlay/* | sort -k1 -hr",
    "enable",
)["messages"]

sudo_ls = eapi.try_eapi_command(
    "bash timeout 2 sudo ls -alSRh /.overlay",
    "enable",
)["messages"]

sudo_lsof = eapi.try_eapi_command(
    "bash timeout 30 sudo lsof -nP | grep '(deleted)'",
    "enable",
)["messages"]


def json_to_file(filename, json_source):
    new_filename = f"{output_dir}/{switch_hostname.strip()}_{filename}"
    with open(new_filename, "w") as my_file:
        if filename.startswith("sudo"):
            for each_line in json_source:
                my_file.write("%s\n" % each_line)
        else:
            my_file.write(json_source)
        print(f"Outputs written to {new_filename}")


json_to_file("sudo_du.txt", sudo_du)
json_to_file("sudo_ls.txt", sudo_ls)
json_to_file("sudo_lsof.txt", sudo_lsof)

netlib.cleanup_log_if_empty(logger_full_path)