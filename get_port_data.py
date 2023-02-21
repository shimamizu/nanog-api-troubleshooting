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
    import re
    import sys
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
    "-p", "--port", type=str, required=True, metavar="32/1", help="The port to look at"
)
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
port_name = args.port
output_dir = args.output_directory
username, password = netlib.get_credentials("TACACS")


start_logger = netlib.setup_logging("port_data", output_dir)
logger = start_logger[0]
logger_full_path = start_logger[1]


eapi = netlib.AristaPyeapi(username, password, switch_hostname, logger)

port_name_long = f"Ethernet{port_name}"
if "/1" in port_name:
    base_port = re.sub(r"\/1$", "", port_name)
    dash2 = re.sub(r"\/1$", "/2", port_name_long)
    dash3 = re.sub(r"\/1$", "/3", port_name_long)
    dash4 = re.sub(r"\/1$", "/4", port_name_long)
else:
    base_port = port_name
    dash2 = base_port
    dash3 = base_port
    dash4 = base_port


def show_switch_version():
    show_version = eapi.get_version()
    switch_version_table = PrettyTable()
    switch_version_table.field_names = [
        "Hostname",
        "Model",
        "OS Version",
        "Serial Number",
    ]
    switch_version_table.add_row(
        [
            hostname_short,
            show_version["model"],
            show_version["eos_version"],
            show_version["serial_number"],
        ]
    )
    print("")
    print(switch_version_table)


def interface_inventory(base_port, port_name_long):
    get_interface_inventory = eapi.get_inventory("interfaces")[base_port]
    inventory_vendor = get_interface_inventory["mfgName"]
    port_inventory_table = PrettyTable()
    port_inventory_table.field_names = [
        "Hostname",
        "Port",
        "Manufacturer",
        "Model",
        "Serial Number",
    ]
    port_inventory_table.add_row(
        [
            hostname_short,
            port_name_long,
            inventory_vendor,
            get_interface_inventory["modelName"],
            get_interface_inventory["serialNum"],
        ]
    )
    print("")
    print(f"{hostname_short} # show inventory | inc {port_name}")
    print(port_inventory_table)
    return inventory_vendor


def interface_errors(port_name_long):
    get_errors = eapi.try_eapi_command("show interfaces counters errors", "enable")[
        "interfaceErrorCounters"
    ][port_name_long]
    interface_counters_table = PrettyTable()
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
    interface_counters_table.add_row(
        [
            port_name_long,
            get_errors["fcsErrors"],
            get_errors["alignmentErrors"],
            get_errors["symbolErrors"],
            get_errors["inErrors"],
            get_errors["frameTooShorts"],
            get_errors["frameTooLongs"],
            get_errors["outErrors"],
        ]
    )
    print(f"\n{hostname_short}# show interfaces counters errors")
    print(interface_counters_table)


def interface_transceiver(port_name_long, dash2, dash3, dash4):
    get_interface_transceiver = eapi.try_eapi_command(
        "show interfaces transceiver", "enable"
    )["interfaces"]
    transceiver_results_table = PrettyTable()
    transceiver_results_table.field_names = [
        "Port",
        "Temp(C)",
        "Voltage",
        "Bias Current",
        "Tx (dBm)",
        "Rx (dBm)",
    ]

    def get_transceiver(port):
        levels = get_interface_transceiver[port]
        transceiver_results_table.add_row(
            [
                port,
                levels["temperature"],
                levels["voltage"],
                levels["txBias"],
                levels["txPower"],
                levels["rxPower"],
            ]
        )

    get_transceiver(port_name_long)
    if "/1" in port_name_long:
        get_transceiver(dash2)
        get_transceiver(dash3)
        get_transceiver(dash4)
    print("")
    print(f"{hostname_short}# show interfaces transceiver")
    transceiver_results_table.float_format = ".2"
    print(transceiver_results_table)


def mac_details(port_name):
    mac_detail_command = f"show interfaces Ethernet {port_name} mac detail"
    get_mac_detail = eapi.try_eapi_command(mac_detail_command, "enable", "text")
    print(f"\n{hostname_short}# {mac_detail_command}")
    print(get_mac_detail)


show_version = eapi.get_version()
hostname_short = eapi.get_hostname_short()
lookup_lldp_command = str(f"show lldp neighbors Ethernet {port_name}")
results_lldp = eapi.try_eapi_command(lookup_lldp_command, "enable")["lldpNeighbors"]
current_port_status = eapi.get_interfaces_status()[port_name_long]
current_port_desc = current_port_status["description"]
current_port_link_status = current_port_status["linkStatus"]
current_port_line_protocol = current_port_status["lineProtocolStatus"]
if not results_lldp:
    # if LLDP returned no data, print an error to the screen and the log file
    print(
        f"\nATTN: {port_name} has no LLDP neighbor. Current description: {current_port_desc}"
    )
    print(
        f"Current link status: {current_port_link_status} line protocol status: {current_port_line_protocol}"
    )
    logger.warning(
        f"{switch_hostname} {port_name} has no LLDP neighbor. Current description: {current_port_desc}"
    )
else:
    # get the neighbor information from LLDP
    my_neighbor_port_long = results_lldp[0]["neighborPort"]
    my_neighbor_port = my_neighbor_port_long.replace("Ethernet", "Et")
    my_neighbor_port = my_neighbor_port_long.replace("Management", "Ma")
    my_neighbor_device = results_lldp[0]["neighborDevice"]
    lldp_neighbor_table = PrettyTable()
    lldp_neighbor_table.field_names = [
        "Hostname",
        "Local Port",
        "LLDP Neighbor",
        "Remote Port",
    ]
    lldp_neighbor_table.add_row(
        [hostname_short, port_name_long, my_neighbor_device, my_neighbor_port_long]
    )
    print(f"{hostname_short}# show lldp neighbors")
    print(lldp_neighbor_table)

print("\n**************************************************************************")
show_switch_version()
inventory_vendor = interface_inventory(base_port, port_name_long)
interface_errors(port_name_long)
if "Mellanox" not in inventory_vendor and "Amphenol" not in inventory_vendor:
    interface_transceiver(port_name_long, dash2, dash3, dash4)
mac_details(port_name)

print("**************************************************************************")

if (
    results_lldp
    and "netapp" not in my_neighbor_device
    and "Mellanox" not in inventory_vendor
    and "Amphenol" not in inventory_vendor
):
    eapi.reset(username, password, my_neighbor_device, logger)

    port_name = my_neighbor_port.replace("Ethernet", "")
    port_name_long = f"Ethernet{port_name}"
    hostname_short = eapi.get_hostname_short()
    if "/1" in port_name:
        base_port = re.sub(r"\/1$", "", port_name)
        dash2 = re.sub(r"\/1$", "/2", port_name_long)
        dash3 = re.sub(r"\/1$", "/3", port_name_long)
        dash4 = re.sub(r"\/1$", "/4", port_name_long)
    else:
        base_port = port_name
    show_switch_version()
    interface_inventory(base_port, port_name_long)
    interface_errors(port_name_long)
    interface_transceiver(port_name_long, dash2, dash3, dash4)
    mac_details(port_name)

netlib.cleanup_log_if_empty(logger_full_path)
