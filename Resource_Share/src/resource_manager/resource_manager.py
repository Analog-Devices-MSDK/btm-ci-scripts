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
import socket
import glob
import json
import os
import random
import subprocess
from datetime import datetime
from typing import Dict, List, Set, Tuple

# pylint: disable=import-error
from tabulate import tabulate


class ResourceManager:
    # pylint: disable=too-many-public-methods,dangerous-default-value
    """BTM-CI Resource Manager"""

    ENV_RESOURCE_LOCK_DIR = "RESOURCE_LOCK_DIR"
    ENV_CI_BOARD_CONFIG = "CI_BOARD_CONFIG"
    ENV_CI_BOARD_CONFIG_CUSTOM = "CI_BOARD_CONFIG_CUSTOM"

    def __init__(self, timeout=60, owner="", extra_resources: List[str] = []) -> None:
        # Initialize the resource file
        self.timeout = timeout
        self.resources = self._add_base_config()
        self.owner = owner
        self._add_custom_config(extra_resources)
        self._add_resources_path()
        self.resource_lock_dir = os.environ.get(self.ENV_RESOURCE_LOCK_DIR)
        self._add_lockdir()

    def _add_lockdir(self):
        if not os.path.exists(self.resource_lock_dir):
            os.mkdir(self.resource_lock_dir)

    def _add_resources_path(self):
        resource_files = os.getenv("RESOURCE_FILES")

        if not resource_files:
            return

        resources = resource_files.split(":")
        for resource in resources:
            self.resources.update(self._get_config(resource))

    def _get_config(self, filepath):
        if not os.path.exists(filepath):
            return {}

        with open(filepath, "r", encoding="utf-8") as config_file:
            try:
                config = json.load(config_file)
            except json.decoder.JSONDecodeError:
                print("Error parsing json from file! returning empty json")
                return {}

        return config

    def _get_base_resource_path(self):
        return os.environ.get(self.ENV_CI_BOARD_CONFIG)

    def _get_custom_resource_path(self):
        return os.environ.get(self.ENV_CI_BOARD_CONFIG_CUSTOM)

    def _get_base_config(self):
        base_resource_path = self._get_base_resource_path()
        return self._get_config(base_resource_path)

    def _get_custom_config(self):
        custom_resource_filepath = os.environ.get(self.ENV_CI_BOARD_CONFIG_CUSTOM)
        return self._get_config(custom_resource_filepath)

    def _add_base_config(self):
        base_resource_path = self._get_base_resource_path()

        if not base_resource_path:
            if os.getlogin() == "btm-ci":
                print("Warning! BOARD CONFIG Environment Variable DOES NOT EXIST!")
            return {}

        return self._get_config(base_resource_path)

    def _add_custom_config(self, extra_resources: List[str]):
        custom_resource_filepath = self._get_custom_resource_path()
        if custom_resource_filepath is not None:
            extra_resources.append(custom_resource_filepath)

        for resource in extra_resources:
            custom_resources = self._get_config(resource)
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

    def get_owned_resources(self, owner: str) -> List[str]:
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

        resources = self.get_owned_resources(owner)

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

    def _update_config(self, new_config: Dict, filepath: str):
        old_config = self._get_config(filepath)
        old_config.update(new_config)
        with open(filepath, "w", encoding="utf-8") as config_file:
            json.dump(old_config, config_file)

    def add_item(self, item: str, filepath: str = "", delimiter="."):
        """Add item to config file

        Parameters
        ----------
        item : str
            Item string (ex: board_name.serial_num=1234)
        filepath : str, optional
            Filepath to write item to, by default ""
            If empty, function will write to baseconfig first.
            If baseconfig does not exist, it will atempt to use the custom file.
            If all paths exhausted the new item will not be written
        Raises: AttributeError
            If config failed to write to any path
        """
        value: str
        key, value = item.split("=")
        key = key.strip()

        key_tree = key.split(delimiter)

        base = key_tree.pop()
        sub_item = {base: value.strip()}

        while key_tree:
            base = key_tree.pop()
            sub_item = {base: sub_item}

        base_resource_path = self._get_base_resource_path()
        custom_resource_path = self._get_custom_resource_path()

        if filepath is not None and os.path.exists(filepath):
            self._update_config(sub_item, filepath=filepath)
        elif filepath:
            with open(filepath, "w", encoding="utf-8") as new_config:
                json.dump(sub_item, new_config)
        elif base_resource_path and os.path.exists(base_resource_path):
            self._update_config(new_config=sub_item, filepath=base_resource_path)
        elif custom_resource_path and os.path.exists(custom_resource_path):
            self._update_config(new_config=sub_item, filepath=custom_resource_path)
        else:
            raise AttributeError(
                "Could not find an applicable config file to write to!"
            )

    def get_dapsn(self, resource: str) -> str:
        """Get Dap serial number as found in board config

        Parameters
        ----------
        resource : str
            Name of resource to get dap sn from

        Returns
        -------
        str
           dap sn
        """
        return self.get_item_value(f"{resource}.dap_sn")

    def get_target(self, resource: str) -> str:
        """Get target chip from resource

        Parameters
        ----------
        resource : str
            Resource name

        Returns
        -------
        str
            target associated with resource
        """
        return self.get_item_value(f"{resource}.target")

    def get_ocdports(self, resource: str) -> str:
        """_summary_

        Parameters
        ----------
        resource : str
            _description_

        Returns
        -------
        str
            _description_
        """
        gdb = self.get_item_value(f"{resource}.ocdports.gdb")
        telnet = self.get_item_value(f"{resource}.ocdports.telnet")
        tcl = self.get_item_value(f"{resource}.ocdports.tcl")

        return gdb, telnet, tcl

    def _get_item_value(self, item_name: str, delimiter=".") -> str:
        """Get value attached to json item

        Parameters
        ----------
        item_name : strans
            json item value
        """
        tree = item_name.split(delimiter)

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

    def get_item_value(self, item_name: str, default: str = "", delimiter=".") -> str:
        """Get value attached to json item

        Parameters
        ----------
        item_name : str
           json item value
        default : str, optional
            default return if value not found, by default ""
        delimiter : str, optional
            Delimiter used to seperate query (ie '.' in item.subitem), by default "."

        Returns
        -------
        str
            Value found in json or default
        """
        try:
            return self._get_item_value(item_name, delimiter=delimiter)
        except KeyError:
            return default

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

    def print_applicable_items(self, target: str = "", group: str = "") -> List[str]:
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
            try:
                if target:
                    if self.get_item_value(f"{rname}.target") != target.upper():
                        continue
                if group:
                    if self.get_item_value(f"{rname}.group") != group.upper():
                        continue
            except KeyError:
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

        return []

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

    def get_switch_config(self, resource: str) -> Tuple[str, str]:
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
        model = self.get_item_value(f"{resource}.sw_model")
        port = self.get_item_value(f"{resource}.sw_state")

        return model, port

    def _generate_3digit_str(self) -> str:
        lower = 10 ** (2)
        upper = 10**3 - 1
        return str(random.randint(lower, upper))

    def _is_port_in_use(self, port: str) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            try:
                sock.bind(("localhost", int(port)))
            except OSError:
                return True

            return False

    def _is_ocd_capable(self, resource):
        if resource not in self.resources:
            return False

        info = self.resources[resource]
        if "dap_sn" not in info:
            return False

        if "ocdports" in info:
            return True

        rand_digits = self._generate_3digit_str()

        gdb = f"3{rand_digits}"
        tcl = f"4{rand_digits}"
        telnet = f"5{rand_digits}"

        while (
            self._is_port_in_use(gdb)
            or self._is_port_in_use(tcl)
            or self._is_port_in_use(telnet)
        ):
            rand_digits = self._generate_3digit_str()
            gdb = f"3{rand_digits}"
            tcl = f"4{rand_digits}"
            telnet = f"6{rand_digits}"

        self.resources[resource]["ocdports"] = {
            "gdb": f"3{rand_digits}",
            "tcl": f"4{rand_digits}",
            "telnet": f"5{rand_digits}",
        }

        return True

    def _get_ocdpath(self):
        return os.getenv("OPENOCD_PATH")

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
        ocdpath = self._get_ocdpath()
        target = self.get_target(resource_name)
        dapsn = self.get_dapsn(resource_name)
        gdb, telnet, tcl = self.get_ocdports(resource_name)

        command = [
            "openocd",
            "-s",
            ocdpath,
            "-f",
            "interface/cmsis-dap.cfg",
            "-f",
            f"target/{target.lower()}.cfg",
            "-c",
            f"adapter serial {dapsn}",
            "-c",
            f"gdb_port {gdb}",
            "-c",
            f"telnet_port {telnet}",
            "-c",
            f"tcl_port {tcl}",
            "-c",
            "init; reset; exit",
        ]

        return subprocess.run(command, check=True).returncode

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

        ocdpath = self._get_ocdpath()
        target = self.get_target(resource_name)
        dapsn = self.get_dapsn(resource_name)
        gdb, telnet, tcl = self.get_ocdports(resource_name)
        common_command = [
            "openocd",
            "-s",
            ocdpath,
            "-f",
            "interface/cmsis-dap.cfg",
            "-f",
            f"target/{target.lower()}.cfg",
            "-c",
            f"adapter serial {dapsn}",
            "-c",
            f"gdb_port {gdb}",
            "-c",
            f"telnet_port {telnet}",
            "-c",
            f"tcl_port {tcl}",
        ]

        if target.lower() == "max32655":
            command = common_command + [
                "-c",
                "init; reset halt; max32xxx mass_erase 0;",
                "-c",
                "exit",
            ]
        else:
            command = common_command + [
                "-c",
                "init; reset halt; max32xxx mass_erase 0; max32xxx mass_erase 1;",
                "-c",
                "exit",
            ]

        return subprocess.run(command, check=False).returncode

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

        ocdpath = os.getenv("OPENOCD_PATH")
        dapsn = self.get_dapsn(resource_name)
        gdb, telnet, tcl = self.get_ocdports(resource_name)
        target = self.get_target(resource_name).lower()

        command = [
            "openocd",
            "-s",
            ocdpath,
            "-f",
            "interface/cmsis-dap.cfg",
            "-f",
            f"target/{target}.cfg",
            "-c",
            f"adapter serial {dapsn}",
            "-c",
            f"gdb_port {gdb}",
            "-c",
            f"telnet_port {telnet}",
            "-c",
            f"tcl_port {tcl}",
            "-c",
            f"program {elf_file} verify; reset; exit",
        ]

        return subprocess.run(command, check=False).returncode

    def clean_environment(self):
        """Erase all boards and delete all locks"""
        for resource in self.resources:
            try:
                self.resource_erase(resource, self.get_owner(resource))
            except AttributeError:
                pass

        self.unlock_all_resources()
