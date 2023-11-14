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
    import os
    from datetime import timedelta

    from dateutil.relativedelta import relativedelta
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
start_logger = netlib.setup_logging("port_data", output_dir)
logger = start_logger[0]
logger_full_path = start_logger[1]

ping_results = netlib.util.check_ping(switch_hostname)

if ping_results < 10:
    # instantiate the eAPI library
    eapi = netlib.AristaPyeapi(username, password, switch_hostname, logger)

    show_version = eapi.get_version()
    reload_cause = eapi.get_reload_cause()
    if reload_cause["resetCauses"]:
        reload_reason = reload_cause["resetCauses"][0]["description"]
        reload_timestamp = str(
            datetime.datetime.utcfromtimestamp(
                reload_cause["resetCauses"][0]["timestamp"]
            )
        )
        now = datetime.datetime.utcnow()
        then = datetime.datetime.utcfromtimestamp(
            reload_cause["resetCauses"][0]["timestamp"]
        )
        difference = str(timedelta(seconds=(now - then).total_seconds()))
        rel_diff = relativedelta(now, then)
        reload_recommendation = reload_cause["resetCauses"][0]["recommendedAction"]
    show_version_uptime = show_version["uptime"]
    show_version_uptime = str(timedelta(seconds=show_version_uptime))

    print(f"Hostname: {switch_hostname}")
    print(
        f'Model: {show_version["model"]} '
        f'Hardware Revision: {show_version["hardware_rev"]}'
    )
    print(f'Serial Number: {show_version["serial_number"]}')
    print(f'OS Version: {show_version["eos_version"]}')

    console = Console()
    reload_table = Table(show_header=False)
    reload_table.add_column("Query", justify="left")
    reload_table.add_column("Data", justify="left", max_width=40)

    reload_table.add_row(
        "Reload Reason",
        reload_reason,
    )
    reload_table.add_row(
        "Recommendation",
        reload_recommendation,
    )
    reload_table.add_row(
        "Last Reboot Date (UTC)",
        reload_timestamp,
    )
    reload_table.add_row(
        "Time Since Last Reboot",
        difference,
    )
    reload_table.add_row(
        "Total Current Uptime",
        show_version_uptime,
    )

    if reload_cause["resetCauses"]:
        console.print(reload_table)
        print(
            "Switch online for:",
            rel_diff.years,
            "years,",
            rel_diff.months,
            "months,",
            rel_diff.days,
            "days,",
            rel_diff.hours,
            "hours,",
            rel_diff.minutes,
            "minutes",
        )
        if "debugInfo" in reload_cause["resetCauses"][0]:
            print("Debug Information will be written to debug.txt file.")
            with open("debug.txt", "w") as file:
                for each_line in reload_cause["resetCauses"][0]["debugInfo"]:
                    file.write("%s\n" % each_line)
        else:
            print("No debug information available")
    else:
        print("No information available about reload.")
elif ping_results >= 10:
    print(f"{switch_hostname} is not pinging, please check console and inspect device.")

netlib.cleanup_log_if_empty(logger_full_path)
