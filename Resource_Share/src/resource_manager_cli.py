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
import glob
import json
import os
import subprocess
import sys
from datetime import datetime
from typing import Dict, List, Set, Tuple

# pylint: disable=import-error
from tabulate import tabulate

from resource_manager import ResourceManager

VERSION = "1.0.0"


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

    return parser.parse_args()


def main():
    """
    MAIN
    """
    # pylint: disable=too-many-branches

    args = config_cli()

    lock_boards = set(args.lock)
    unlock_boards = set(args.unlock)
    resource_manager = ResourceManager(timeout=int(args.timeout))

    if args.clean_env:
        resource_manager.clean_environment()

    if args.list_usage:
        resource_manager.print_usage()

    if args.unlock_all:
        print("Unlocking all boards!")
        resource_manager.unlock_all_resources()
        sys.exit(0)

    if lock_boards:
        print(f"Attempting to lock all boards {lock_boards}")

        could_lock = resource_manager.lock_resources(lock_boards, args.owner)

        if could_lock:
            print("Successfully locked boards")
            sys.exit(0)
        else:
            print("Failed to lock all boards")
            sys.exit(-1)

    if unlock_boards:
        print(f"Unlocking resources {unlock_boards}")
        resource_manager.unlock_resources(unlock_boards, args.owner)

    if args.unlock_owner:
        unlocked_resources = resource_manager.unlock_resource_by_owner(
            args.unlock_owner
        )
        print(f"Unlocked {len(unlocked_resources)} resources")
        for resource in unlocked_resources:
            print(resource)

    if args.get_value:
        print(resource_manager.get_item_value(args.get_value))

    if args.get_owner:
        print(resource_manager.get_owner(args.get_owner))

    if args.version:
        print(VERSION)

    if args.owner_resources:
        resources = resource_manager.get_owned_boards(args.owner_resources)
        for resource in resources:
            print(resource)

    if args.find_board is not None:
        resource_manager.print_applicable_items(
            target=args.find_board[0], group=args.find_board[1]
        )

    sys.exit(0)


if __name__ == "__main__":
    main()
