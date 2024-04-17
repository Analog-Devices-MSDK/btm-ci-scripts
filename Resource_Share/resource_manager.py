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
import os
import sys
import json
from typing import List
from datetime import datetime


class ResourceManager:
    """BTM-CI Resource Manager"""

    def __init__(self, resource_filepath: str = None, timeout=60) -> None:
        # Initialize the resource file
        resource_filepath = os.environ.get("CI_BOARD_CONFIG")
        with open(resource_filepath, "r", encoding="utf-8") as resource_file:
            self.resources: dict = json.load(resource_file)

        if resource_filepath is not None:
            custom_resource_filepath = resource_filepath
            with open(custom_resource_filepath, "r", encoding="utf-8") as resource_file:
                self.resources.update(json.load(resource_file))

        self.timeout = timeout
        self.resource_lock_dir = os.environ.get("RESOURCE_LOCK_DIR")

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

    def get_resource_start_time(self, resource: str):
        lockfile_path = self.get_lock_path(resource)
        if not os.path.exists(lockfile_path):
            return "N/A"
        else:
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

            resource_used[resource] = [in_use, start_time]

        return resource_used

    def get_lock_path(self, resource: str):
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

    def unlock_resources(self, resources: str):
        for resource in resources:
            self.unlock_resource(resource)

    def unlock_all_resources(self):
        self.unlock_resources(self.resources.keys())

    def lock_resource(self, resource: str):
        lockfile_path = self.get_lock_path(resource)

        if not os.path.exists(lockfile_path):
            with open(lockfile_path, "w", encoding="utf-8") as lockfile:

                now = datetime.now()
                dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

                lockfile.writelines([dt_string])

            return True

        return False

    def lock_resources(self, resources: List[str]) -> bool:
        """
        Create resource lock
        """
        resource_locks = {resource: False for resource in resources}

        start = datetime.now()
        idx = 0
        while resources:
            resource = resources[idx]
            lock_ok = self.lock_resource(resource)

            if lock_ok:
                resource_locks[resource] = True
                resources.remove(resource)

            now = datetime.now()

            if (now - start).total_seconds() > self.timeout:
                # TIMEOUT!
                break

        if len(resources) == 0:
            return True

        for resource in resource_locks:
            self.unlock_resource(resource)

        return False

    def get_item_value(self, item_name: str) -> str:
        """Get value attached to json item

        Parameters
        ----------
        item_name : str
            item name

        Returns
        -------
        str
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
