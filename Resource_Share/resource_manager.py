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
from typing import Dict, List, Set

# pylint: disable=import-error
from tabulate import tabulate

# pylint: enable=import-error


class ResourceManager:
    """BTM-CI Resource Manager"""

    ENV_RESOURCE_LOCK_DIR = "RESOURCE_LOCK_DIR"
    ENV_CI_BOARD_CONFIG = "CI_BOARD_CONFIG"
    ENV_CI_BOARD_CONFIG_CUSTOM = "CI_BOARD_CONFIG_CUSTOM"

    def __init__(self, timeout=60) -> None:
        # Initialize the resource file
        self.timeout = timeout
        self.resources = self._add_base_config()
        self._add_custom_config()
        self.resource_lock_dir = os.environ.get(self.ENV_RESOURCE_LOCK_DIR)
        self._add_lockdir()

    def _add_lockdir(self):
        if not os.path.exists(self.resource_lock_dir):
            os.mkdir(self.resource_lock_dir)

    def _add_base_config(self):
        base_resource_path = os.environ.get(self.ENV_CI_BOARD_CONFIG)
        with open(base_resource_path, "r", encoding="utf-8") as resource_file:
            resources = json.load(resource_file)
        return resources

    def _add_custom_config(self):
        custom_resource_filepath = os.environ.get(self.ENV_CI_BOARD_CONFIG_CUSTOM)
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
        lockfile_path = self.get_lock_path(resource)
        return os.path.exists(lockfile_path)

    def get_resource_lock_info(self, resource: str) -> Dict[str, object]:
        """Get lockfile info associated to locked resource

        Parameters
        ----------
        resource : str
            Resource name

        Returns
        -------
        Dict[str, object]
            Dictionary of lockfile information
        """

        lock_path = self.get_lock_path(resource)
        if not os.path.exists(lock_path):
            return {}
        with open(lock_path, "r", encoding="utf-8") as lockfile:
            lf_info = json.load(lockfile)
        return lf_info

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
            resource_info = self.get_resource_lock_info(resource)

            resource_used[resource] = {
                "in-use": in_use,
                "group": self.resources[resource].get("group"),
                "start": resource_info.get("start", ""),
                "owner": resource_info.get("owner", ""),
            }

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

    def unlock_resource(self, resource: str, owner="") -> bool:
        """Unlock resource

        Parameters
        ----------
        resource : str
            Resource name found in board config or custom config
        owner : str, optional
            Owner who originally locked the board, by default ""

        Returns
        -------
        bool
            True unlocked. False if lockfile exists but owner does not match

        Raises
        ------
        ValueError
            If resource does not exist or lockfile does not exist
        """
        if resource not in self.resources:
            raise ValueError(
                f"Resource {resource} not found in either the board config or custom config"
            )

        lock = self.get_lock_path(resource)

        if not os.path.exists(lock):
            raise ValueError("Lockfile does not exist")

        created_owner = self.get_resource_lock_info(resource)["owner"]

        if created_owner not in ("", owner):
            print("You do not own the lockfile! Will not delete")
            return False

        os.remove(lock)

        return True

    def unlock_resources(self, resources: Set[str], owner="") -> int:
        """Unlock a list of resources

        Parameters
        ----------
        resources : Set[str]
            Set of resources to unlock
        """
        unlock_count = 0
        for resource in resources:
            if self.unlock_resource(resource, owner):
                unlock_count += 1
        return unlock_count

    def unlock_all_resources(self):
        """Delete all lockfiles"""
        locks = glob.glob(f"{self.resource_lock_dir}/*")
        for lock in locks:
            print(f"Unlocking - {os.path.basename(lock)}")
            os.remove(lock)

    def lock_resource(self, resource: str, owner="") -> bool:
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
        if resource not in self.resources:
            raise ValueError(
                f"Resource {resource} not found in either the board config or custom config"
            )

        lockfile_path = self.get_lock_path(resource)

        if not self.resource_in_use(resource):
            with open(lockfile_path, "w", encoding="utf-8") as lockfile:
                now = datetime.now()

                lf_info = {"start": now.strftime("%d/%m/%Y %H:%M:%S"), "owner": owner}

                json.dump(lf_info, lockfile)

            return True

        return False

    def lock_resources(self, resources: Set[str], owner="") -> bool:
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
        locked_boards = []
        while not boards_locked:
            unlocked_count = 0
            for resource in resources:
                if not self.resource_in_use(resource):
                    unlocked_count += 1
            # Attempt to lock them all at once
            if unlocked_count == len(resources):
                lockcount = 0
                for resource in resources:
                    lockcount += 1 if self.lock_resource(resource, owner) else 0
                    locked_boards.append((resource, owner))
                    boards_locked = True

            now = datetime.now()
            if (now - start).total_seconds() > self.timeout:
                # TIMEOUT!
                break

        # if we failed to lock all the boards, release the ones we locked
        if boards_locked and lockcount != len(resources):
            for resource, resource_owner in locked_boards:
                rm.unlock_resource(resource, resource_owner)
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
            raise ValueError("Tree could not be parsed!")

        # Get the first input
        arg = tree.pop(0)
        if arg in self.resources:
            ans = self.resources[arg]
        else:
            raise KeyError(f"Could not find {arg} in resources")

        # while we havent fully traversed the tree keep going
        while tree:
            arg = tree.pop(0)
            if arg in ans:
                ans = ans[arg]
            else:
                raise KeyError(f"Could not find {arg} in resources")

        # whatever is at the end is the answer
        return ans

    def get_applicable_items(self, target: str = None, group: str = None) -> List[str]:
        """Get items that match criteria of group and target

        Parameters
        ----------
        target : str, optional
            Target type, by default None
        group : str, optional
            Group target should be in, by default None

        Returns
        -------
        List[str]
            Resources matching criteria

        """
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

        return applicable_items

    def print_usage(self):
        """Pretty print the resource usage"""

        header = ["NAME"]
        usage = self.get_resource_usage()
        resources = list(usage.keys())

        header.extend(usage.get(resources[0]).keys())
        header = [x.upper() for x in header]

        table = [header]

        for resource, data in usage.items():
            row = [resource]
            row.extend(list(data.values()))
            table.append(row)

        print(tabulate(table, headers="firstrow", tablefmt="fancy_grid"))

    def _is_ocd_capable(self, resource):
        if resource not in self.resources:
            return False

        info = self.resources[resource]
        if "dap_sn" not in info:
            return False
        if "ocdports" not in info:
            return False

        return True

    def resource_reset(self, resource_name: str) -> bool:
        """Reset resource found in board_config.json or custom config

        Parameters
        ----------
        resource_name : str
            Name of resource to reset
        """
        if not self._is_ocd_capable(resource_name):
            raise AttributeError(
                f"Resource {resource_name} does not contain the info to reset."
                ""
                """Requires dap_sn and ocdports"""
            )

        with subprocess.Popen(["bash", "-c", f"ocdreset {resource_name}"]) as process:
            process.wait()

        return process.returncode == 0

    def resource_erase(self, resource_name: str):
        """Erase resource found in board_config.json or custom config

        Parameters
        ----------
        resource_name : str
            Name of resource to erase
        """
        if not self._is_ocd_capable(resource_name):
            raise AttributeError(
                f"""Resource {resource_name} does not contain the info to erase."""
                """Requires dap_sn and ocdports"""
            )

        with subprocess.Popen(["bash", "-c", f"ocderase {resource_name}"]) as process:
            process.wait()

        return process.returncode == 0

    def resource_flash(self, resource_name: str, elf_file: str):
        """Flash a resource in board_config.json or custom config with given elf
        Parameters
        ----------
        resource_name : str
            Resource to flash
        elf_file : str
            Elf file to program resource with
        """
        if not self._is_ocd_capable(resource_name):
            raise AttributeError(
                f"""Resource {resource_name} does not contain the info to flash."""
                """Requires dap_sn and ocdports"""
            )

        with subprocess.Popen(
            ["bash", "-c", f"ocdflash {resource_name} {elf_file}"]
        ) as process:
            process.wait()

        return process.returncode == 0

    def clean_environment(self):
        """Erase all boards and delete all locks"""
        for resource in self.resources:
            try:
                self.resource_erase(resource)
            except AttributeError:
                pass

        self.unlock_all_resources()


if __name__ == "__main__":
    # Setup the command line description text
    DESC_TEXT = """
    Lock/Unlock Hardware resources
    Query resource information
    Monitor resources
    """

    # Parse the command line arguments
    parser = argparse.ArgumentParser(
        description=DESC_TEXT, formatter_class=argparse.RawTextHelpFormatter
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
        "--owner",
        default="",
        help="Name of user locking or unlocking",
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

    parser.add_argument(
        "-go",
        "--get-owner",
        default="",
        help="Get owner of resource if locked",
    )

    parser.add_argument(
        "--clean-env",
        action="store_true",
        help="Delete all locks and erase all boards with a programmable feature",
    )

    args = parser.parse_args()

    lock_boards = set(args.lock)
    unlock_boards = set(args.unlock)

    rm = ResourceManager(timeout=int(args.timeout))

    if args.clean_env:
        rm.clean_environment()

    if args.list_usage:
        rm.print_usage()

    if args.unlock_all:
        print("Unlocking all boards!")
        rm.unlock_all_resources()
        sys.exit(0)

    if lock_boards:
        print(f"Attempting to lock all boards {lock_boards}")

        COULD_LOCK = rm.lock_resources(lock_boards, args.owner)

        if COULD_LOCK:
            print("Successfully locked boards")
            sys.exit(0)
        else:
            print("Failed to lock all boards")
            sys.exit(-1)

    if unlock_boards:
        print(f"Unlocking resources {unlock_boards}")
        rm.unlock_resources(unlock_boards, args.owner)

    if args.get_value:
        print(rm.get_item_value(args.get_value))

    if args.get_owner:
        print(rm.get_resource_lock_info(args.get_owner).get("owner", ""))

    sys.exit(0)
