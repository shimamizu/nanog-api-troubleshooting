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
    import os
    import re

    from rich.console import Console
    from rich.table import Table

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

console = Console()

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
    switch_version_table = Table()
    switch_version_table.add_column(
        "Hostname", justify="left", style="magenta", no_wrap=True, vertical="middle"
    )
    switch_version_table.add_column("Model", justify="center", no_wrap=True)
    switch_version_table.add_column("OS\nVersion", justify="center", no_wrap=True)
    switch_version_table.add_column("Serial\nNumber", justify="center", no_wrap=True)

    switch_version_table.add_row(
        hostname_short,
        show_version["model"],
        show_version["eos_version"],
        show_version["serial_number"],
    )
    print("")
    console.print(switch_version_table)


def interface_inventory(base_port, port_name_long):
    get_interface_inventory = eapi.get_inventory("interfaces")[base_port]
    inventory_vendor = get_interface_inventory["mfgName"]
    port_inventory_table = Table()
    port_inventory_table.add_column(
        "Hostname", justify="left", style="magenta", no_wrap=True, vertical="middle"
    )
    port_inventory_table.add_column("Port", justify="center", no_wrap=True)
    port_inventory_table.add_column("Manufacturer", justify="center", no_wrap=True)
    port_inventory_table.add_column("Model", justify="center", no_wrap=True)
    port_inventory_table.add_column("Serial\nNumber", justify="center", no_wrap=True)

    port_inventory_table.add_row(
        hostname_short,
        port_name_long,
        inventory_vendor,
        get_interface_inventory["modelName"],
        get_interface_inventory["serialNum"],
    )
    print("")
    print(f"{hostname_short} # show inventory | inc {port_name}")
    console.print(port_inventory_table)
    return inventory_vendor


def interface_errors(port_name_long):
    get_errors = eapi.try_eapi_command("show interfaces counters errors", "enable")[
        "interfaceErrorCounters"
    ][port_name_long]
    interface_counters_table = Table()
    interface_counters_table.add_column(
        "Port", justify="left", style="magenta", no_wrap=True
    )
    interface_counters_table.add_column("FCS", justify="center", no_wrap=True)
    interface_counters_table.add_column("Align", justify="center", no_wrap=True)
    interface_counters_table.add_column("Symbol", justify="center", no_wrap=True)
    interface_counters_table.add_column("RX", justify="center", no_wrap=True)
    interface_counters_table.add_column("Runts", justify="center", no_wrap=True)
    interface_counters_table.add_column("Giants", justify="center", no_wrap=True)
    interface_counters_table.add_column("TX", justify="center", no_wrap=True)

    interface_counters_table.add_row(
        port_name_long,
        str(get_errors["fcsErrors"]),
        str(get_errors["alignmentErrors"]),
        str(get_errors["symbolErrors"]),
        str(get_errors["inErrors"]),
        str(get_errors["frameTooShorts"]),
        str(get_errors["frameTooLongs"]),
        str(get_errors["outErrors"]),
    )
    print(f"\n{hostname_short}# show interfaces counters errors")
    console.print(interface_counters_table)


def interface_transceiver(port_name_long, dash2, dash3, dash4):
    get_interface_transceiver = eapi.try_eapi_command(
        "show interfaces transceiver", "enable"
    )["interfaces"]
    transceiver_results_table = Table()
    transceiver_results_table.add_column(
        "Port", justify="left", style="magenta", no_wrap=True
    )
    transceiver_results_table.add_column("Temp(C)", justify="center", no_wrap=True)
    transceiver_results_table.add_column("Voltage", justify="center", no_wrap=True)
    transceiver_results_table.add_column("Bias Current", justify="center", no_wrap=True)
    transceiver_results_table.add_column("Tx (dBm)", justify="center", no_wrap=True)
    transceiver_results_table.add_column("Rx (dBm)", justify="center", no_wrap=True)

    def get_transceiver(port):
        levels = get_interface_transceiver[port]
        transceiver_results_table.add_row(
            port,
            f'{levels["temperature"]:.2f}',
            f'{levels["voltage"]:.2f}',
            f'{levels["txBias"]:.2f}',
            f'{levels["txPower"]:.2f}',
            f'{levels["rxPower"]:.2f}',
        )

    get_transceiver(port_name_long)
    if "/1" in port_name_long:
        get_transceiver(dash2)
        get_transceiver(dash3)
        get_transceiver(dash4)
    print("")
    print(f"{hostname_short}# show interfaces transceiver")
    transceiver_results_table.float_format = ".2"
    console.print(transceiver_results_table)


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
        f"\nATTN: {port_name} has no LLDP neighbor. "
        f"Current description: {current_port_desc}"
    )
    print(
        f"Current link status: {current_port_link_status} line protocol "
        f"status: {current_port_line_protocol}"
    )
    logger.warning(
        f"{switch_hostname} {port_name} has no LLDP neighbor. "
        f"Current description: {current_port_desc}"
    )
else:
    # get the neighbor information from LLDP
    my_neighbor_port_long = results_lldp[0]["neighborPort"]
    my_neighbor_port = my_neighbor_port_long.replace("Ethernet", "Et")
    my_neighbor_port = my_neighbor_port_long.replace("Management", "Ma")
    my_neighbor_device = results_lldp[0]["neighborDevice"]
    lldp_neighbor_table = Table()
    lldp_neighbor_table.add_column(
        "Hostname", justify="left", style="magenta", no_wrap=True, vertical="middle"
    )
    lldp_neighbor_table.add_column("Local Port", justify="center")
    lldp_neighbor_table.add_column("LLDP Neighbor", justify="left")
    lldp_neighbor_table.add_column("Remote Port", justify="center")
    lldp_neighbor_table.add_row(
        hostname_short, port_name_long, my_neighbor_device, my_neighbor_port_long
    )
    print(f"{hostname_short}# show lldp neighbors")
    console.print(lldp_neighbor_table)

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
