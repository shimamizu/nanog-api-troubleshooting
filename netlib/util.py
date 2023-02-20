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
import getpass
import logging
import os
import sys


def setup_logging(script_function, output_dir=os.environ.get("HOME", "/tmp")):
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    print(f"\nIf log entries are present, the file will be saved under: {output_dir}\n")
    script_time_stamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    log_filename = f"{output_dir}/{script_function}_log_{script_time_stamp}.log"
    logger = logging.getLogger(script_function)
    # create file handler which logs even debug messages
    fh = logging.FileHandler(log_filename)
    fh.setLevel(logging.WARNING)
    # create formatter and add it to the handlers
    formatter = logging.Formatter("%(asctime)-15s %(levelname)-8s %(message)s")
    fh.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    return [logger, log_filename]


def cleanup_log_if_empty(logger_full_path):
    logging.shutdown()
    if os.stat(logger_full_path).st_size == 0:
        print(f"\nLog file was empty, removing file: {logger_full_path}")
        os.remove(logger_full_path)
    else:
        print(f"\nScript has log entries, find log here: {logger_full_path}")


def get_credentials(prefix="TACACS"):
    # Usage example:
    # username, password = get_credentials()
    try:
        user = os.environ.get(f"{prefix}_USERNAME", None)
        if user is None:
            user = input(f"Enter your {prefix} username: ")
        password = os.environ.get(f"{prefix}_PASSWORD", None)
        if password is None:
            password = getpass.getpass(
                prompt=f"{prefix} password for {user}: ",
            )
        return (user, password)
    except KeyboardInterrupt:
        print("\n\nCaught Keyboard Interrupt - Exiting the program.")
        sys.exit()
