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

try:
    # importing libraries
    import argparse
    import datetime
    import logging
    import os
    import sys
    from datetime import timedelta
    from getpass import getpass

    from prettytable import PrettyTable

    import netlib
except ImportError as error:
    print(error)
    quit()
except Exception as exception:
    print(exception)

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
start_logger = netlib.setup_logging("get_fpga_errors", output_dir)
logger = start_logger[0]
logger_full_path = start_logger[1]

# instantiate the eAPI library
eapi = netlib.AristaPyeapi(username, password, switch_hostname, logger)

show_version = eapi.get_version()
fpga_error = eapi.try_eapi_command("show hardware fpga error", "enable")
fpga_uncorrected = fpga_error["uncorrectableCrcs"]

version = show_version["eos_version"]
serial_number = show_version["serial_number"]
model = show_version["model"]
hardware_rev = show_version["hardware_rev"]
uptime = str(timedelta(seconds=show_version["uptime"]))

print(f"Hostname: {switch_hostname}")
print(f"Model: {model}, Hardware Revision: {hardware_rev}")
print(f"Serial Number: {serial_number}")
print(f"OS Version: {version}")
print(f"Uptime: {uptime}")

fpga_table = PrettyTable()
fpga_table.field_names = [
    "Query",
    "Data",
]

fpga_table.header = False
fpga_table.align["Query"] = "l"
fpga_table.align["Data"] = "l"

for value in fpga_uncorrected:
    error_count = fpga_error_count = fpga_uncorrected[value]["count"]
    fpga_table.add_row(
        [
            f"{value} Error Count",
            error_count,
        ]
    )
    if error_count > 0:
        fpga_error_first = str(
            datetime.datetime.utcfromtimestamp(
                fpga_uncorrected[value]["firstOccurrence"]
            )
        )
        fpga_error_last = str(
            datetime.datetime.utcfromtimestamp(
                fpga_uncorrected[value]["lastOccurrence"]
            )
        )
        fpga_table.add_row(
            [
                f"{value} First Occurence (UTC)",
                fpga_error_first,
            ]
        )
        fpga_table.add_row(
            [
                f"{value} Last Occurence (UTC)",
                fpga_error_last,
            ]
        )

fpga_table.sortby = "Query"
print(fpga_table)

netlib.cleanup_log_if_empty(logger_full_path)
