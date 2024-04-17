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

defaultTimeout = 60

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

parser.add_argument("lockFile", help="Filename to lock or unlock")
parser.add_argument(
    "--timeout",
    "-t",
    default=defaultTimeout,
    help="Timeout before returning in seconds",
)
parser.add_argument(
    "--lock", "-l", action="store_true", help="Lock the file, otherwise unlock the file"
)

args = parser.parse_args()

if args.lock:
    toSeconds = int(args.timeout)
    while toSeconds:
        if os.path.exists(args.lockFile):
            time.sleep(1)
            toSeconds = toSeconds - 1

            if toSeconds == 0:
                print("Timed out waiting for lockFile to be released")
                sys.exit(1)

        else:
            toSeconds = 0

    # Create the lock file
    Path(args.lockFile).touch()

else:
    # Test to see if the file exists
    if not os.path.exists(args.lockFile):
        print("Lock file does not exits")

if args.lock:
    # Open the file
    lockfile = open(args.lockFile, "r+")

    # Write the PID to the file
    lockfile.truncate(0)
    lockfile.write(str(os.getpid()) + "\n")

    # Close the file
    lockfile.close()

else:
    # Delete the file
    if os.path.exists(args.lockFile):
        os.remove(args.lockFile)

sys.exit(0)
