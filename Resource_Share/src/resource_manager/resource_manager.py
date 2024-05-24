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
import glob
import json
import os
import subprocess
from datetime import datetime
from typing import Dict, List, Set, Tuple

# pylint: disable=import-error
from tabulate import tabulate


class ResourceManager:
    """BTM-CI Resource Manager"""

    ENV_RESOURCE_LOCK_DIR = "RESOURCE_LOCK_DIR"
    ENV_CI_BOARD_CONFIG = "CI_BOARD_CONFIG"
    ENV_CI_BOARD_CONFIG_CUSTOM = "CI_BOARD_CONFIG_CUSTOM"

    def __init__(self, timeout=60, owner="") -> None:
        # Initialize the resource file
        self.timeout = timeout
        self.resources = self._add_base_config()
        self.owner = owner
        self._add_custom_config()
        self.resource_lock_dir = os.environ.get(self.ENV_RESOURCE_LOCK_DIR)
        self._add_lockdir()

    def _add_lockdir(self):
        if not os.path.exists(self.resource_lock_dir):
            os.mkdir(self.resource_lock_dir)

    def _add_base_config(self):
        base_resource_path = os.environ.get(self.ENV_CI_BOARD_CONFIG)

        if not base_resource_path:
            if os.getlogin() == "btm-ci":
                print("Warning! BOARD CONFIG Environment Variable DOES NOT EXIST!")
            return {}

        with open(base_resource_path, "r", encoding="utf-8") as resource_file:
            resources = json.load(resource_file)
        return resources

    def _add_custom_config(self):
        custom_resource_filepath = os.environ.get(self.ENV_CI_BOARD_CONFIG_CUSTOM)
        if custom_resource_filepath is not None:
            with open(custom_resource_filepath, "r", encoding="utf-8") as resource_file:
                custom_resources = json.load(resource_file)
                self.resources.update(custom_resources)

    def get_owner(self, resource: str) -> str:
        """Get the current owner of a resource

        Parameters
        ----------
        resource : str
            Name of resource

        Returns
        -------
        str
            Owner
        """
        return self.get_resource_lock_info(resource).get("owner", "")

    def get_owned_boards(self, owner: str) -> List[str]:
        """Get resources owned by specific owner

        Parameters
        ----------
        owner : str
            Owner name

        Returns
        -------
        List[str]
            Resources owned by given owner

        Raises
        ------
        ValueError
            If owner is an empty string
        """
        if owner == "":
            raise ValueError("Owner must not be empty")
        resources = []

        for resource in self.resources:
            current_owner = self.get_owner(resource)

            if owner == current_owner:
                resources.append(resource)

        return resources

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
                "locked": in_use,
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

    def unlock_resource_by_owner(self, owner: str) -> List[str]:
        """Unlock all resources allocated to owner

        Parameters
        ----------
        owner : str
            Owner

        Returns
        -------
        List[str]
            Resources unlocked

        Raises
        ------
        ValueError
            If owner is an empty string
        """
        if owner == "":
            raise ValueError("Owner must not be empty")

        resources = self.get_owned_boards(owner)

        self.unlock_resources(resources, owner)

        return resources

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
                self.unlock_resource(resource, resource_owner)
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
            
     
        

    def print_applicable_items(
        self, target: str = "", group: str = ""
    ) -> List[str]:
        """Print an item that matches criteria of group and target

        Parameters
        ----------
        target : str, optional
            Target type, by default None
        group : str, optional
            Group target should be in, by default None

        Returns
        -------
        None

        """
        applicable_items_open = []
        applicable_items_inuse = []
        for rname in self.resources:
            if target :
                if self.get_item_value(f"{rname}.target") != target.upper():
                    continue
            if group:
                if self.get_item_value(f"{rname}.group") != group.upper():
                    continue

            if self.resource_in_use(rname):
                applicable_items_inuse.append(rname)
            else:
                applicable_items_open.append(rname)
        applicable_items = []
        applicable_items.extend(applicable_items_open)
        applicable_items.extend(applicable_items_inuse)
        if applicable_items:
            print(" ".join(applicable_items))
            return []
        print("")

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

    def get_switch_config(self, resource:str) -> Tuple[str, str]:
        """Get Switch configuration

        Parameters
        ----------
        resource : str
            _description_

        Returns
        -------
        Tuple[str, str]
            _description_
        """
        model = self.get_item_value(f'{resource}.sw_model')
        port =  self.get_item_value(f'{resource}.sw_state')

        return model, port

    def _is_ocd_capable(self, resource):
        if resource not in self.resources:
            return False

        info = self.resources[resource]
        if "dap_sn" not in info:
            return False
        if "ocdports" not in info:
            return False

        return True

    def resource_reset(self, resource_name: str, owner: str = "") -> bool:
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
        
        owner = owner if owner != "" else self.owner

        with subprocess.Popen(
            ["bash", "-c", f"ocdreset {resource_name} {owner}"]
        ) as process:
            process.wait()

        return process.returncode == 0

    def resource_erase(self, resource_name: str, owner: str = ""):
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
        owner = owner if owner != "" else self.owner

        with subprocess.Popen(
            ["bash", "-c", f"ocderase {resource_name} {owner}"]
        ) as process:
            process.wait()

        return process.returncode == 0

    def resource_flash(self, resource_name: str, elf_file: str, owner: str = ""):
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
        if not os.path.exists(elf_file):
            raise ValueError(f"ELF FILE DNE {elf_file}")

        owner = owner if owner != "" else self.owner

        with subprocess.Popen(
            ["bash", "-c", f"ocdflash {resource_name} {elf_file} {owner}"]
        ) as process:
            process.wait()

        return process.returncode == 0

    def clean_environment(self):
        """Erase all boards and delete all locks"""
        for resource in self.resources:
            try:
                self.resource_erase(resource, self.get_owner(resource))
            except AttributeError:
                pass

        self.unlock_all_resources()