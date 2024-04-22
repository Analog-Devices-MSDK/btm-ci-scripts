#! /usr/bin/env python3
###############################################################################
#
# Copyright (C) 2022-2023 Maxim Integrated Products, Inc., All Rights Reserved.
# (now owned by Analog Devices, Inc.)
#
# This software is protected by copyright laws of the United States and
# of foreign countries. This material may also be protected by patent laws
# and technology transfer regulations of the United States and of foreign
# countries. This software is furnished under a license agreement and/or a
# nondisclosure agreement and may only be used or reproduced in accordance
# with the terms of those agreements. Dissemination of this information to
# any party or parties not specified in the license agreement and/or
# nondisclosure agreement is expressly prohibited.
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL MAXIM INTEGRATED BE LIABLE FOR ANY CLAIM, DAMAGES
# OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# Except as contained in this notice, the name of Maxim Integrated
# Products, Inc. shall not be used except as stated in the Maxim Integrated
# Products, Inc. Branding Policy.
#
# The mere transfer of this software does not imply any licenses
# of trade secrets, proprietary technology, copyrights, patents,
# trademarks, maskwork rights, or any other form of intellectual
# property whatsoever. Maxim Integrated Products, Inc. retains all
# ownership rights.
#
###############################################################################
#
# Copyright (C) 2023 Analog Devices, Inc. All Rights Reserved.
#
# This software is proprietary and confidential to Analog Devices, Inc. and
# its licensors.
#
###############################################################################
"""
resource_manager.py

Description: BTM-CI Resource Manager

"""
import argparse
import glob
import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Set, List


class ResourceManager:
    """BTM-CI Resource Manager"""

    def __init__(self, timeout=60) -> None:
        # Initialize the resource file
        base_resource_path = os.environ.get("CI_BOARD_CONFIG")
        with open(base_resource_path, "r", encoding="utf-8") as resource_file:
            self.resources: dict = json.load(resource_file)

        self._add_custom_config()

        self.timeout = timeout
        self.resource_lock_dir = os.environ.get("RESOURCE_LOCK_DIR")
        self._add_lockdir()

    def _add_lockdir(self):
        if not os.path.exists(self.resource_lock_dir):
            os.mkdir(self.resource_lock_dir)

    def _add_custom_config(self):
        custom_resource_filepath = os.environ.get("CI_BOARD_CONFIG_CUSTOM")
        if custom_resource_filepath is not None:
            with open(custom_resource_filepath, "r", encoding="utf-8") as resource_file:
                custom_resources = json.load(resource_file)
                self.resources.update(custom_resources)

    def resource_in_use(self, resource: str) -> bool:
        """Checks if a lockfile has been place on a resource

        Parameters
        ----------
        resource : str
            resource name

        Returns
        -------
        bool
            True if resource in use. False otherwise
        """
        locks = os.listdir(self.resource_lock_dir)

        return resource in locks

    def get_resource_start_time(self, resource: str) -> str:
        """Get the start time a resource was locked

        Parameters
        ----------
        resource : str
            resource name

        Returns
        -------
        str
            Date and time resource was locked
        """
        lockfile_path = self.get_lock_path(resource)
        if not os.path.exists(lockfile_path):
            return "N/A"

        with open(lockfile_path, "r", encoding="utf-8") as lockfile:
            return lockfile.readline()

    def get_resource_usage(self):
        """Get a dictionary of resources and their usage

        Returns
        -------
        Dict[Str,Bool]
           Resource in use or not
        """
        resource_used = {}
        for resource in self.resources.keys():
            in_use = self.resource_in_use(resource=resource)
            start_time = self.get_resource_start_time(resource)

            resource_used[resource] = [
                in_use,
                start_time,
                self.resources[resource]["group"],
            ]

        return resource_used

    def get_lock_path(self, resource: str) -> str:
        """Get the full path to a lockfile given the resource name

        Parameters
        ----------
        resource : str
            name of resource

        Returns
        -------
        str
            Lockfile path
        """
        return os.path.join(self.resource_lock_dir, resource)

    def unlock_resource(self, resource: str):
        """
        Delete Resource lock

        """
        lock = self.get_lock_path(resource)

        if not os.path.exists(lock):
            return False

        os.remove(lock)

        return True

    def unlock_resources(self, resources: Set[str]):
        """Unlock a list of resources

        Parameters
        ----------
        resources : str
            _description_
        """
        for resource in resources:
            self.unlock_resource(resource)

    def unlock_all_resources(self):
        """Delete all lockfiles"""
        locks = glob.glob(f"{self.resource_lock_dir}/*")
        for lock in locks:
            print(f"Unlocking - {os.path.basename(lock)}")
            os.remove(lock)

    def is_locked(self, resource: str) -> bool:
        """Check if a resource is locked

        Parameters
        ----------
        resource : str
            Name of resource

        Returns
        -------
        bool
            True if locked. False otherwise.
        """
        lockfile_path = self.get_lock_path(resource)
        return os.path.exists(lockfile_path)

    def lock_resource(self, resource: str) -> bool:
        """Lock resource

        Parameters
        ----------
        resource : str
            Resource name

        Returns
        -------
        bool
            True is locked successfully. False otherwise.
        """
        lockfile_path = self.get_lock_path(resource)

        if not self.is_locked(resource):
            with open(lockfile_path, "w", encoding="utf-8") as lockfile:
                now = datetime.now()
                dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

                lockfile.writelines([dt_string])

            return True

        return False

    def lock_resources(self, resources: Set[str]) -> bool:
        """Create locks for resources

        Parameters
        ----------
        resources : Set[str]
            Set of resources to lock

        Returns
        -------
        bool
            True if successfully locked all boards. False otherwise.
        """

        start = datetime.now()

        boards_locked = False
        start = datetime.now()

        while not boards_locked:
            print('Boards locked', boards_locked)
            unlocked_count = 0
            for resource in resources:
                if not self.is_locked(resource):
                    unlocked_count += 1
            # Attempt to lock them all at once
            if unlocked_count == len(resources):
                lockcount = 0
                for resource in resources:
                    lockcount += 1 if self.lock_resource(resource) else 0
                    boards_locked = True

            now = datetime.now()
            if (now - start).total_seconds() > self.timeout:
                # TIMEOUT!
                break

        # if we failed to lock all the boards, release the ones we locked
        if boards_locked and lockcount != len(resources):
            for resource in resources:
                self.unlock_resource(resource)
                boards_locked = False

        return boards_locked

    def get_item_value(self, item_name: str) -> str:
        """Get value attached to json item

        Parameters
        ----------
        item_name : strans
            json item value
        """
        tree = item_name.split(".")

        if not tree:
            print("Tree could not be parsed!")
            sys.exit(-1)

        # Get the first input
        arg = tree.pop(0)
        if arg in self.resources:
            ans = self.resources[arg]
        else:
            print(f"Could not find {arg} in resources")
            sys.exit(-1)

        # while we havent fully traversed the tree keep going
        while tree:
            arg = tree.pop(0)
            if arg in ans:
                ans = ans[arg]
            else:
                print(f"Could not find {item_name} in resources")
                sys.exit(-1)

        # whatever is at the end is the answer
        return ans

    def get_applicable_items(self, target: str = None, group: str = None) -> List[str]:
        applicable_items = []
        for rname in self.resources:
            if self.resource_in_use(rname):
                continue
            if target is not None:
                if self.get_item_value(f"{rname}.target") != target.upper():
                    continue
            if group is not None:
                if self.get_item_value(f"{rname}.group") != group.upper():
                    continue
            applicable_items.append(rname)

        if applicable_items == []:
            raise ValueError("No items matching the criteria found.")

        return applicable_items

    def print_usage(self):
        """Pretty print the resource usage"""
        usage = self.get_resource_usage()
        print(f"{'Board':<35} {'In Use':<15} {'Start Time':<15} {'Group':<15}")
        print("*" * 75)
        for resource, usage_info in usage.items():
            print(
                f"{resource:<35} {str(usage_info[0]):<15} {str(usage_info[1]):<15} {str(usage_info[2]):<15}"
            )
            print("-" * 75)

    @staticmethod
    def resource_reset(resource_name: str):
        """Reset resource found in board_config.json or custom config

        Parameters
        ----------
        resource_name : str
            Name of resource to reset
        """
        with subprocess.Popen(["bash", "-c", f"ocdreset {resource_name}"]) as process:
            process.wait()

    @staticmethod
    def resource_erase(resource_name: str):
        """Erase resource found in board_config.json or custom config

        Parameters
        ----------
        resource_name : str
            Name of resource to erase
        """
        with subprocess.Popen(["bash", "-c", f"ocderase {resource_name}"]) as process:
            process.wait()

    @staticmethod
    def resource_flash(resource_name: str, elf_file: str):
        """Flash a resource in board_config.json or custom config with given elf
        Parameters
        ----------
        resource_name : str
            Resource to flash
        elf_file : str
            Elf file to program resource with
        """
        with subprocess.Popen(
            ["bash", "-c", f"ocdflash {resource_name} {elf_file}"]
        ) as process:
            process.wait()


if __name__ == "__main__":
    # Setup the command line description text
    DESC_TEXTT = """
    Lock/Unlock Hardware resources
    Query resource information
    Monitor resources
    """

    # Parse the command line arguments
    parser = argparse.ArgumentParser(
        description=DESC_TEXTT, formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "--timeout",
        "-t",
        default=60,
        help="Timeout before returning in seconds",
    )
    parser.add_argument(
        "-u",
        "--unlock",
        default=[],
        action="extend",
        nargs="*",
        help="Name of board to unlock per boards_config.json",
    )

    parser.add_argument(
        "--unlock-all",
        action="store_true",
        help="Unlock all resources in lock directory",
    )
    parser.add_argument(
        "-l",
        "--lock",
        default=[],
        action="extend",
        nargs="*",
        help="Name of board to lock per boards_config.json",
    )

    parser.add_argument(
        "--list-usage",
        action="store_true",
        help="""Display basic usage stats of the boards"""
        """including if they are locked and when they were locked""",
    )

    parser.add_argument(
        "-g",
        "--get-value",
        default=None,
        help="Get value for resource in config (ex: max32655_board1.dap_sn)",
    )

    args = parser.parse_args()

    lock_boards = set(args.lock)
    unlock_boards = set(args.unlock)

    rm = ResourceManager(timeout=int(args.timeout))

    if args.list_usage:
        rm.print_usage()

    if args.unlock_all:
        print("Unlocking all boards!")
        rm.unlock_all_resources()
        sys.exit(0)

    if lock_boards:
        print(f"Attempting to lock all boards {lock_boards}")

        COULD_LOCK = rm.lock_resources(lock_boards)

        if COULD_LOCK:
            print("Successfully locked boards")
            sys.exit(0)
        else:
            print("Failed to lock all boards")
            sys.exit(-1)

    if unlock_boards:
        print(f"Unlocking resources {unlock_boards}")
        rm.unlock_resources(unlock_boards)

    if args.get_value:
        print(rm.get_item_value(args.get_value))

    sys.exit(0)
