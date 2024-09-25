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
"""Resource manager command line interface."""
import argparse
import os
import sys
from typing import Dict

# pylint: disable=redefined-builtin
from rich import print

# pylint: enable=redefined-builtin

from resource_manager import ResourceManager

VERSION = "1.0.2"


def config_cli() -> argparse.Namespace:
    """
    Configure CLI
    """
    desc_text = """
    Lock/Unlock Hardware resources
    Query resource information
    Monitor resources
    """

    # Parse the command line arguments
    parser = argparse.ArgumentParser(
        description=desc_text, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="Get application version",
    )
    parser.add_argument(
        "-r",
        "--resources",
        default=[],
        action="extend",
        nargs="*",
        help="List of extra resource files usable to get/add information",
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
        "--lock-all",
        action="store_true",
        help="Unlock all resources in lock directory",
    )
    parser.add_argument(
        "--unlock-all",
        action="store_true",
        help="Lock all resources. Only meant for admin purposes",
    )
    parser.add_argument(
        "-uo",
        "--unlock-owner",
        default="",
        help="Unlock all resources allocated to owner",
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
        "-lu",
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
        "-or",
        "--owner-resources",
        default="",
        help="Get resources allocated to owner",
    )
    parser.add_argument(
        "-f",
        "--find-board",
        nargs=2,
        default=None,
        help="Find a board which matches the criteria TARGET GROUP",
    )
    parser.add_argument(
        "--delimiter",
        default=".",
        help="Delimiter used for get item syntax",
    )
    parser.add_argument(
        "--timeout",
        "-t",
        default=60,
        help="Timeout before returning in seconds",
    )
    parser.add_argument(
        "--owner",
        default="",
        help="Name of user locking or unlocking",
    )
    parser.add_argument(
        "--clean-env",
        action="store_true",
        help="Delete all locks and erase all boards with a programmable feature",
    )

    parser.add_argument(
        "-a",
        "--add-item",
        default="",
        help="Set value for resource in config (ex: max32655_board1.dap_sn=3)",
    )

    parser.add_argument(
        "-p",
        "--purgable",
        action="store_true",
        help="Display purgable resources",
    )

    return parser.parse_args()


def _get_purgable(resource_manager: ResourceManager) -> Dict[str, str]:
    serial_dev_path = "/dev/serial/by-id/"
    if os.path.exists(serial_dev_path):
        serial_devs = os.listdir(serial_dev_path)
    else:
        serial_devs = []

    purgable = {}

    resource: str
    values: dict
    for resource, values in resource_manager.resources.items():
        cport = values.get("console_port")
        cport = os.path.basename(cport)
        if cport and cport not in serial_devs:
            purgable[resource] = "Console port not detected"
            continue

        hciport = values.get("hci_port")
        hciport = os.path.basename(hciport)
        if hciport and hciport not in serial_devs:
            if resource not in purgable:
                purgable[resource] = "HCI port not detected"

    return purgable


def main():
    """
    MAIN
    """
    # pylint: disable=too-many-branches

    args = config_cli()

    lock_resources = set(args.lock)
    unlock_resources = set(args.unlock)

    resource_manager = ResourceManager(
        timeout=int(args.timeout), extra_resources=args.resources
    )

    if args.clean_env:
        resource_manager.clean_environment()

    if args.list_usage:
        resource_manager.print_usage()

    if args.unlock_all:
        print("Unlocking all resources!")
        resource_manager.unlock_all_resources()
        sys.exit(0)
    
    if args.lock_all:
        for resource in resource_manager.resources:
            resource_manager.lock_resource(resource, owner='ADMIN')
            

    if lock_resources:
        print(f"Attempting to lock resources {lock_resources}")

        could_lock = resource_manager.lock_resources(lock_resources, args.owner)

        if could_lock:
            print("Successfully locked resources")
            sys.exit(0)
        else:
            print("Failed to lock resources")
            sys.exit(-1)

    if unlock_resources:
        print(f"Unlocking resources {unlock_resources}")
        resource_manager.unlock_resources(unlock_resources, args.owner)

    if args.unlock_owner:
        unlocked_resources = resource_manager.unlock_resource_by_owner(
            args.unlock_owner
        )
        print(f"Unlocked {len(unlocked_resources)} resources")
        for resource in unlocked_resources:
            print(resource)

    if args.add_item:
        for path in args.resources:
            resource_manager.add_item(args.add_item, path)

    if args.get_value:
        print(resource_manager.get_item_value(args.get_value, delimiter=args.delimiter))

    if args.get_owner:
        print(resource_manager.get_owner(args.get_owner))

    if args.version:
        print(VERSION)

    if args.owner_resources:
        resources = resource_manager.get_owned_resources(args.owner_resources)
        for resource in resources:
            print(resource)

    if args.find_board is not None:
        resource_manager.print_applicable_items(
            target=args.find_board[0], group=args.find_board[1]
        )

    if args.purgable:
        purgable = _get_purgable(resource_manager)
        print("[red]Purgable reosources[/red]")
        for key, value in purgable.items():
            print(key, value)

    sys.exit(0)


if __name__ == "__main__":
    main()
