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

import datetime
import json
import logging
import os
import socket
import sys

import pyeapi

import netlib.util


class AristaPyeapi:
    def __init__(self, username, password, switch_hostname, logger=None, timeout=180):
        self.switch_hostname = switch_hostname.strip()
        self.node = pyeapi.connect(
            transport="https",
            host=self.switch_hostname,
            username=username,
            password=password,
            timeout=timeout,
            return_node=True,
        )
        if logger is None:
            self.logger = netlib.util.setup_logging("generic_eapi")[0]
        else:
            self.logger = logger

    def reset(self, username, password, switch_hostname, logger):
        self.__init__(username, password, switch_hostname, logger)

    def try_eapi_command(
        self,
        command,
        run_method="run_commands",
        encoding_type="json",
    ):
        try:
            pyeapi_log_level = pyeapi.eapilib._LOGGER.getEffectiveLevel()
            pyeapi.eapilib._LOGGER.setLevel(logging.CRITICAL)
            # lower layer function, using enable or config mode is preferred
            if run_method == "run_commands":
                command_output = self.node.run_commands(command)[0]
            # this one is best for getting show commands, use text encoding for getting
            # back the same output as you'd see on the switch screen, default is json
            # which will give you back the json formatted show values for better variable
            # maninpulation with your scripts
            elif run_method == "enable":
                if encoding_type == "json":
                    command_output = self.node.enable(command)[0]["result"]
                elif encoding_type == "text":
                    command_output = self.node.enable(command, encoding="text")[0][
                        "result"
                    ]["output"]
            elif run_method == "config":
                command_output = self.node.config(command)
            elif run_method == "api":
                command_output = eval(command)
            return command_output
        except KeyboardInterrupt:
            print("Caught Keyboard Interrupt - Exiting the program.")
            sys.exit()
        except ImportError as import_error:
            print(f"Could not import module: {import_error}")
            self.logger.warning(f"Import error: {import_error}")
        except json.decoder.JSONDecodeError as json_error:
            print("Received unexpected JSON error, but non impacting. Continuing.")
        except KeyError as key_error:
            print(f"{self.switch_hostname} has a key error.")
            self.logger.warning(
                f"Key error while running script against {self.switch_hostname}."
            )
        except pyeapi.eapilib.CommandError as command_error:
            print(
                f"Command error while executing [{command}] for {self.switch_hostname}:"
            )
            self.logger.warning(
                f"Command error on {self.switch_hostname}: for [{command}]\n {str(command_error.command_error)}"
            )
        except pyeapi.eapilib.ConnectionError as conn_error:
            print(
                f"########## WARNING ##########\nError connecting to the eAPI for {self.switch_hostname}:\n--{str(conn_error.message)}\n#############################"
            )
            self.logger.warning(
                f"Connection error on {self.switch_hostname}:\n--{str(conn_error.message)}"
            )
            if "Name or service not known" in str(conn_error.message):
                sys.exit(1)
        except TypeError as type_error:
            print(f"Ran into a Type error: {type_error}")
            self.logger.warning(
                f"Type error while running scipt against {self.switch_hostname}."
            )
        except Exception as exception:
            print(f"Hit some other exception: {exception}")
            self.logger.warning(
                f"Hit another exception against {self.switch_hostname}.\n {str(exception)}"
            )
        finally:
            if pyeapi_log_level != pyeapi.eapilib._LOGGER.getEffectiveLevel():
                pyeapi.eapilib._LOGGER.setLevel(pyeapi_log_level)

    def cleanup_config_sessions(self):
        config_sessions = self.try_eapi_command(
            "show configuration sessions", "enable"
        )["sessions"]
        for session in config_sessions:
            removal_command = f"no configure session {session}"
            self.try_eapi_command(removal_command, "enable")

    def copy_run_start(self):
        self.try_eapi_command("copy running-config startup-config", "enable")

    def get_arp(self):
        arp_entries = self.try_eapi_command("show ip arp", "enable")["ipV4Neighbors"]
        return arp_entries

    def get_extensions(self):
        extensions = self.try_eapi_command("show extensions", "enable")["extensions"]
        return extensions

    def get_file_date(self, filename):
        get_file_date = self.try_eapi_command(
            f"bash timeout 2 sudo date -r /mnt/flash/{filename}", "enable", "text"
        )
        if get_file_date:
            get_file_date = get_file_date.strip()
        return get_file_date

    def get_flash_storage(self):
        get_flash_storage = self.try_eapi_command("dir flash:", "enable", "text")
        return get_flash_storage

    def get_hostname_short(self):
        hostname_short = self.try_eapi_command("show hostname", "enable")["hostname"]
        return hostname_short

    def get_interface_discards(self):
        get_discards = self.try_eapi_command(
            "show interfaces counters discards", "enable"
        )["interfaces"]
        return get_discards

    def get_interface_errors(self):
        get_errors = self.try_eapi_command("show interfaces counters errors", "enable")[
            "interfaceErrorCounters"
        ]
        return get_errors

    def get_interfaces_status(self):
        interfaces_status = self.try_eapi_command("show interfaces status", "enable")[
            "interfaceStatuses"
        ]
        return interfaces_status

    def get_inventory(self, type):
        inventory = self.try_eapi_command("show inventory", "enable")
        if type == "interfaces":
            return inventory["xcvrSlots"]
        elif type == "power":
            return inventory["powerSupplySlots"]
        elif type == "storage":
            return inventory["storageDevices"]
        elif type == "system":
            return inventory["systemInformation"]
        elif type == "linecards":
            return inventory["cardSlots"]
        else:
            return inventory

    def get_ipv6_neighbors(self):
        ipv6_neighbors = self.try_eapi_command("show ipv6 neighbors", "enable")[
            "ipV6Neighbors"
        ]
        return ipv6_neighbors

    def get_lldp_neighbors(self):
        lldp_neighbors = self.try_eapi_command("show lldp neighbors", "enable")[
            "lldpNeighbors"
        ]
        return lldp_neighbors

    def get_mlag(self):
        mlag_status = self.try_eapi_command("show mlag", "enable")
        state = mlag_status["state"]
        neg_status = mlag_status["negStatus"]
        local_if_status = mlag_status["localIntfStatus"]
        peer_link_status = mlag_status["peerLinkStatus"]
        peer_link = mlag_status["peerLink"]
        peer_address = mlag_status["peerAddress"]
        config_sanity = mlag_status["configSanity"]
        mlag_dict = {
            "state": state,
            "neg_status": neg_status,
            "local_if_status": local_if_status,
            "peer_link_status": peer_link_status,
            "peer_link": peer_link,
            "peer_address": peer_address,
            "config_sanity": config_sanity,
        }
        return mlag_dict

    def get_port_channel(self, port_channel):
        port_channel_num = port_channel.split("Port-Channel")[1]
        port_channel_data = self.try_eapi_command(
            f"show port-channel {port_channel_num}", "enable"
        )["portChannels"][port_channel]
        return port_channel_data

    def get_port_channel_summary(self):
        port_channel_summary = self.try_eapi_command(
            "show port-channel summary", "enable"
        )["portChannels"]
        return port_channel_summary

    def get_power(self):
        power_status = self.try_eapi_command("show environment power", "enable")[
            "powerSupplies"
        ]
        return power_status

    def get_reload_cause(self):
        show_reload_cause = self.try_eapi_command("show reload cause", "enable")
        return show_reload_cause

    def get_revision_number(self, banner_type):
        show_banner = self.try_eapi_command(f"show banner {banner_type}", "enable")
        if banner_type == "login":
            banner = show_banner["loginBanner"]
        elif banner_type == "motd":
            banner = show_banner["motd"]
        if banner:
            try:
                revision = banner.split("revision ")[1]
                revision = revision.split()[0]
            except:
                revision = "wrong"
        else:
            revision = "missing"
        return revision

    def get_storage(self):
        get_storage = self.try_eapi_command(
            "bash timeout 2 sudo df -lh", "enable", "text"
        )
        return get_storage

    def get_storage_overlay(self):
        get_storage_overlay = self.try_eapi_command(
            "bash timeout 2 sudo df -lh /.overlay", "enable", "text"
        )
        return get_storage_overlay

    def get_version(self):
        show_version = self.try_eapi_command("show version", "enable")
        switch_eos_version = show_version["version"]
        switch_hardware_rev = show_version["hardwareRevision"]
        switch_model = show_version["modelName"]
        switch_serial_number = show_version["serialNumber"]
        switch_system_mac = show_version["systemMacAddress"]
        switch_uptime = show_version["uptime"]
        if switch_eos_version.startswith(("4.19", "4.20")) is True:
            switch_cli_commands = "old"
        else:
            switch_cli_commands = "new"
        show_version_dict = {
            "eos_version": switch_eos_version,
            "hardware_rev": switch_hardware_rev,
            "model": switch_model,
            "serial_number": switch_serial_number,
            "system_mac": switch_system_mac,
            "uptime": switch_uptime,
            "cli_commands": switch_cli_commands,
        }
        return show_version_dict

    def get_vrf(self):
        which_commands = self.get_version()["cli_commands"]
        if which_commands == "old":
            configured_vrfs = self.try_eapi_command("show vrf", "enable", "text")
            if "management" in configured_vrfs:
                vrf = "management"
            else:
                vrf = "default"
        elif which_commands == "new":
            configured_vrfs = self.try_eapi_command("show vrf", "enable")
            if "management" in configured_vrfs["vrfs"]:
                vrf = "management"
            else:
                vrf = "default"
        else:
            vrf = "default"
        return vrf

    def peer_supervisor_command(self, peer_command):
        run_peer_command = self.try_eapi_command(
            f'bash timeout 10 Cli -p15 -c "session peer-supervisor {peer_command}"',
            "enable",
            "text",
        )
        return run_peer_command

    def set_lacp_timeout(self, port_channel, timeout_value):
        set_command = f'self.node.api("interfaces").set_lacp_timeout("Port-Channel{port_channel}", {timeout_value})'
        result = self.try_eapi_command(set_command, "api")
        return result
