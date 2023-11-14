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

    from termcolor import colored

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
start_logger = netlib.setup_logging("get_mlag", output_dir)
logger = start_logger[0]
logger_full_path = start_logger[1]

# instantiate the eAPI library
eapi = netlib.AristaPyeapi(username, password, switch_hostname, logger)

show_mlag = eapi.get_mlag()

mlag_neg_status = show_mlag["neg_status"]
mlag_peer_link = show_mlag["peer_link"]
mlag_peer_link_status = show_mlag["peer_link_status"]
mlag_state = show_mlag["state"]
if mlag_peer_link_status == "up":
    mlag_config_sanity = show_mlag["config_sanity"]
    print(f"Mlag Config Sanity: {mlag_config_sanity}")

print(f"Mlag Peer Link: {mlag_peer_link}")
print(f"Mlag Peer Link Status: {mlag_peer_link_status}")
print(f"Mlag Negotiation Status: {mlag_neg_status}")
print(f"Mlag State: {mlag_state}")


show_port_channel = eapi.get_port_channel(mlag_peer_link)
port_channel_active_ports = show_port_channel["activePorts"]
port_channel_inactive_ports = show_port_channel["inactivePorts"]
print("\nActive Ports: ")
for port in port_channel_active_ports:
    print(colored(port, "green"))
print("\nInactive Ports: ")
for port in port_channel_inactive_ports:
    print(colored(port, "red"))

netlib.cleanup_log_if_empty(logger_full_path)
