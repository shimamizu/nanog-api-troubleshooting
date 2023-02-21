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
    import time
    from getpass import getpass

    import numpy as np
    import pyeapi
    from prettytable import PrettyTable

    import netlib
except ImportError as error:
    print(error)
    quit()
except Exception as exception:
    print(exception)


def read_the_errors():
    get_errors = eapi.get_interface_errors()
    interface_counters_table = PrettyTable()
    interface_counters_table.title = "show interfaces counters errors | nz"
    interface_counters_table.field_names = [
        "Port",
        "FCS",
        "Align",
        "Symbol",
        "Rx",
        "Runts",
        "Giants",
        "Tx",
    ]
    interface_errors_array = {}
    number_of_errors = 0
    for interface in get_errors:
        interface_errors = get_errors[interface]
        port_alignment_errors = interface_errors["alignmentErrors"]
        port_fcs_errors = interface_errors["fcsErrors"]
        port_frame_too_longs = interface_errors["frameTooLongs"]
        port_frame_too_shorts = interface_errors["frameTooShorts"]
        port_in_errors = interface_errors["inErrors"]
        port_out_errors = interface_errors["outErrors"]
        port_symbol_errors = interface_errors["symbolErrors"]
        if (
            port_alignment_errors != 0
            or port_fcs_errors != 0
            or port_frame_too_longs != 0
            or port_frame_too_shorts != 0
            or port_in_errors != 0
            or port_out_errors != 0
            or port_symbol_errors != 0
        ):
            number_of_errors += 1
            interface_counters_table.add_row(
                [
                    interface,
                    port_fcs_errors,
                    port_alignment_errors,
                    port_symbol_errors,
                    port_in_errors,
                    port_frame_too_shorts,
                    port_frame_too_longs,
                    port_out_errors,
                ]
            )
            interface_errors_array[interface] = [
                port_fcs_errors,
                port_alignment_errors,
                port_symbol_errors,
                port_in_errors,
                port_frame_too_shorts,
                port_frame_too_longs,
                port_out_errors,
            ]
    if number_of_errors > 0:
        print(interface_counters_table)
    else:
        print(f"No errors seen currently for {hostname_short}.")
    return interface_errors_array


def read_the_discards():
    get_discards = eapi.get_interface_discards()
    interface_discard_array = {}
    interface_discard_table = PrettyTable()
    interface_discard_table.title = "show interfaces counters discards | nz"
    interface_discard_table.field_names = ["Port", "In Discards", "Out Discards"]
    number_of_discards = 0
    for interface in get_discards:
        interface_discards = get_discards[interface]
        port_in_discards = interface_discards["inDiscards"]
        port_out_discards = interface_discards["outDiscards"]
        if port_in_discards != 0 or port_out_discards != 0:
            number_of_discards += 1
            interface_discard_table.add_row(
                [interface, port_in_discards, port_out_discards]
            )
            interface_discard_array[interface] = [port_in_discards, port_out_discards]
    if number_of_discards > 0:
        print(interface_discard_table)
    else:
        print(f"No discards seen currently for {hostname_short}.")
    return interface_discard_array


parser = argparse.ArgumentParser()
parser.add_argument(
    "-s",
    "--switches",
    type=str,
    required=True,
    metavar="switches.txt",
    help="A list of switch hostnames (FQDN) one per line",
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
switch_list = open(args.switches)
output_dir = args.output_directory
username, password = netlib.get_credentials("TACACS")

# open a file for logging errors
start_logger = netlib.setup_logging("get_errors_and_discards", output_dir)
logger = start_logger[0]
logger_full_path = start_logger[1]

all_switch_errors = {}
all_switch_discards = {}

print("Please wait while first scans for all complete.")

for switch_hostname in switch_list:
    # instantiate the eAPI library
    eapi = netlib.AristaPyeapi(username, password, switch_hostname, logger)
    hostname_short = eapi.get_hostname_short()
    current_time = datetime.datetime.fromtimestamp(time.time()).strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    print(
        "\n#######################################################################################"
    )
    print(
        f"Checking {hostname_short} for errors and discards the first time @ {current_time}"
    )
    print(
        "#######################################################################################\n"
    )

    try:
        all_switch_errors[hostname_short] = read_the_errors()
        all_switch_discards[hostname_short] = read_the_discards()

        current_time = datetime.datetime.fromtimestamp(time.time()).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        print(
            "\n#######################################################################################"
        )
        print(
            f"Checking {hostname_short} for errors and discards again @ {current_time}"
        )
        print(
            "#######################################################################################\n"
        )
        # get_errors = eapi.try_eapi_command("show interfaces counters errors", "enable")[
        #     "interfaceErrorCounters"
        # ]
        # get_discards = eapi.try_eapi_command(
        #     "show interfaces counters discards", "enable"
        # )["interfaces"]

        second_interface_errors_array = read_the_errors()
        second_interface_discard_array = read_the_discards()
        compare_interface_errors_change = {}
        compare_interface_discards_change = {}
        for interface in all_switch_errors[hostname_short]:
            compare_interface_errors_change[interface] = np.subtract(
                second_interface_errors_array[interface],
                all_switch_errors[hostname_short][interface],
            )
        for interface in all_switch_discards[hostname_short]:
            compare_interface_discards_change[interface] = np.subtract(
                second_interface_discard_array[interface],
                all_switch_discards[hostname_short][interface],
            )
        for interface in compare_interface_errors_change:
            int_values = compare_interface_errors_change[interface]
            if np.any(int_values):
                print("!!!!!!!!!!!!!!!!!!!! ATTENTION !!!!!!!!!!!!!!!!!!!!")
                print(
                    f"Interface: {interface} saw new errors. FCS: {str(int_values[0])} Alignment: {str(int_values[1])} Symbol: {str(int_values[2])} Rx: {str(int_values[3])} Runts: {str(int_values[4])} Giants: {str(int_values[5])} Tx: {str(int_values[6])}"
                )
        for interface in compare_interface_discards_change:
            int_values = compare_interface_discards_change[interface]
            if np.any(int_values):
                print("!!!!!!!!!!!!!!!!!!!! ATTENTION !!!!!!!!!!!!!!!!!!!!")
                print(
                    f"Interface: {interface} saw new discards. Discards In: {str(int_values[0])} Discards Out: {str(int_values[1])}"
                )

    except KeyboardInterrupt:
        print("Caught Keyboard Interrupt - Exiting the program.")
        sys.exit()

netlib.cleanup_log_if_empty(logger_full_path)
