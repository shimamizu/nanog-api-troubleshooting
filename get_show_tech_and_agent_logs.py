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
    import logging
    import os
    import sys
    import tarfile
    from datetime import datetime
    from getpass import getpass
    from pathlib import Path

    import pexpect
    import pyeapi

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
    "-t",
    "--ticket",
    type=str,
    required=True,
    metavar="123456",
    help="Ticket number (INC or SR)",
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
ticket_number = args.ticket
output_dir = args.output_directory
username, password = netlib.get_credentials("TACACS")

# open a file for logging errors
start_logger = netlib.setup_logging("get_show_tech", output_dir)
logger = start_logger[0]
logger_full_path = start_logger[1]

# instantiate the eAPI library
eapi = netlib.AristaPyeapi(username, password, switch_hostname, logger)
logs_time_stamp = datetime.now().strftime("%Y-%m-%d_%H:%M:%S")

try:
    time_start = datetime.now()
    switch_hostname_short = eapi.get_hostname_short()
    base_filename = f"{ticket_number}_{switch_hostname_short}_{logs_time_stamp}_"
    print("Generating show tech-support file.")
    show_tech = eapi.try_eapi_command("show tech-support", "enable", "text")
    print("Generating show agent logs file.")
    agent_logs = eapi.try_eapi_command("show agent logs", "enable")["output"]
    print("Generating show agent qtrace file.")
    qtrace_filename = f"{base_filename}agent_qtrace.log.gz"
    eapi.try_eapi_command(
        f"show agent qtrace | gzip >/mnt/flash/{qtrace_filename}", "enable", "text"
    )
    print("Zipping up /var/qt/log into a tar.")
    qtlog_filename = f"{base_filename}qt_logs.tar.gz"
    eapi.try_eapi_command(
        f"bash timeout 10 sudo tar -czvf - /var/log/qt/ > /mnt/flash/{qtlog_filename}",
        "enable",
        "text",
    )
    print("Zipping up /mnt/flash/schedule/tech-support/* into a tar.")
    historical_techs_filename = f"{base_filename}historical_techs.tar.gz"
    eapi.try_eapi_command(
        f"bash timeout 10 tar -cvf - /mnt/flash/schedule/tech-support/* > /mnt/flash/{historical_techs_filename}",
        "enable",
        "text",
    )
    print("Generating show logging system file.")
    logging_system = eapi.try_eapi_command("show logging system", "enable")["output"]
    print("Generating show aaa accounting logs file.")
    aaa_accounting = eapi.try_eapi_command("show aaa accounting logs", "enable")[
        "output"
    ]
    print("Generating output for bash df -h.")
    disk_free = eapi.try_eapi_command("bash timeout 2 df -h", "enable")["messages"]
    print("Generating output for dir all-filesystems.")
    dir_all_file_sys = eapi.try_eapi_command("dir all-filesystems ", "enable")[
        "messages"
    ]

except KeyboardInterrupt:
    print("Caught Keyboard Interrupt - Exiting the program.")
    sys.exit()

array_of_files = []


def json_to_file(filename, json_source):
    new_filename = f"{output_dir}/{ticket_number}_{switch_hostname_short}_{logs_time_stamp}_{filename}"
    with open(new_filename, "w") as my_file:
        if filename == "disk_free.txt" or filename == "dir_all_filesystems.txt":
            for each_line in json_source:
                my_file.write("%s\n" % each_line)
        else:
            my_file.write(json_source)
        print(f"Saved {new_filename} to this server.")
        array_of_files.append(new_filename)


def scp_transfer(filename):
    scp_command = f"scp {username}@{switch_hostname}:/mnt/flash/{filename} {output_dir}"
    print(f"Attempting to SCP {filename} from the switch to this server.")
    try:
        pexpect.run(scp_command)
        child = pexpect.spawn(scp_command)
        child.expect(".*assw.*")
        child.sendline(password)
        child.expect(pexpect.EOF, timeout=5)
    except Exception as exception:
        print(f"WARNING!! Copy failed for {filename}: please check logs!")
        logger.warning(f"{switch_hostname} copy failed: {str(exception)}")
    else:
        print(f"Copy successful for {filename}.")
        print(f"Removing {filename} from the switch /mnt/flash now")
        eapi.try_eapi_command(f"delete flash:{filename}", "enable")
        array_of_files.append(f"{output_dir}/{filename}")


scp_transfer(qtrace_filename)
scp_transfer(qtlog_filename)
scp_transfer(historical_techs_filename)

json_to_file("tech_support.txt", show_tech)
json_to_file("disk_free.txt", disk_free)
json_to_file("agent_logs.txt", agent_logs)
json_to_file("logging_system.txt", logging_system)
json_to_file("aaa_accounting.txt", aaa_accounting)
json_to_file("dir_all_filesystems.txt", dir_all_file_sys)


try:
    tar = tarfile.open(f"{output_dir}/{base_filename}tac_pack.tar.gz", "w:gz")
    for tac_file in array_of_files:
        tar.add(tac_file)
    tar.close()
except Exception as exception:
    print(exception)
else:
    print(
        f"Successfully tar'ed up all files into {output_dir}/{base_filename}tac_pack.tar.gz and now removing individual files."
    )
    for tac_file in array_of_files:
        os.remove(tac_file)
    print(f"Done! Please don't forget to upload this TAC pack to Arista.")
    time_finish = datetime.now()
    time_end = (time_finish - time_start).total_seconds()
    print(
        "{}: Took {:.2f} seconds to copy all needed files for TAC.".format(
            switch_hostname, time_end
        )
    )

netlib.cleanup_log_if_empty(logger_full_path)
