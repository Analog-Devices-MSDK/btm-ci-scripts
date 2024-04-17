#! /usr/bin/env python3

################################################################################
# Copyright (C) 2020 Maxim Integrated Products, Inc., All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
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

## Resource_Share.py
#
# Share hardware resources with lock files.
#

import sys
import argparse
import os
from pathlib import Path
import time
import json
import time
from resource_manager import ResourceManager


# Setup the command line description text
descText = """
Share hardware resources with lock files.

This tool creates lock files and prevents resource contention. Calling this will block
until the resource can be locked or times out waiting.

return values:
0: Success
1: Timeout waiting for lock to release
2: Trying to unlock a file that doesn't exits
"""

# Parse the command line arguments
parser = argparse.ArgumentParser(
    description=descText, formatter_class=argparse.RawTextHelpFormatter
)


parser.add_argument(
    "--timeout",
    "-t",
    default=60,
    help="Timeout before returning in seconds",
)
parser.add_argument(
    "--unlock", "-ul", action="store_true", help="Unlock the file, otherwise lock the file"
)
parser.add_argument(
    "--unlock-all",  action="store_true", help="Unlock the file, otherwise lock the file"
)
parser.add_argument(
    "-b",
    "--board",
    action="extend",
    nargs="*",
    help="Name of board to lock per boards_config.json"
)

args = parser.parse_args()
boards = list(args.board)

rm = ResourceManager()

if args.unlock_all:
    print('Unlocking all boards!')
    rm.unlock_all_resources()
    sys.exit(0)

if not args.unlock:
    print(f"Attempting to lock all boards {boards}")
    could_lock = rm.lock_resources(boards)
    if(could_lock):
        print("Successfully locked boards")
        sys.exit(0)
    else:
        print("Failed to lock all boards")
        sys.exit(-1)
else:
    print(f"Unlocking resources {boards}")
    rm.unlock_resources(boards)
    


sys.exit(0)
