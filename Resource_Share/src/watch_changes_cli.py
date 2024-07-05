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
import subprocess
import sys
from typing import List

VERSION = "1.0.0"


def config_cli() -> argparse.Namespace:
    """
    Configure CLI
    """
    desc_text = """
    Check for changes in git repo compared to list of watch files
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
        "-w",
        "--watch-files",
        default=[],
        action="extend",
        nargs="*",
        help="List of watch files",
    )

    parser.add_argument(
        "-f",
        "--file",
        default=None,
        help="File containing directories and files to watch",
    )
    parser.add_argument(
        "-p",
        "--watch-path",
        default=".",
        help="Path to git repo to diff",
    )

    return parser.parse_args()


def get_changed_folders() -> List[str]:
    """Get changed folders

    Returns
    -------
    List[str]
        Changed folders
    """
    try:
        # Run the git diff command
        result = subprocess.run(
            # ['git', 'diff', '--dirstat=files,0', 'HEAD~1'],
            ["git", "ls-files", "--other", "--modified", "--exclude-standard"],
            capture_output=True,
            text=True,
            check=True,
        )

        # Process the output
        output = result.stdout
        # Use sed-like processing in Python to extract the folder names
        folders = [line.split()[-1] for line in output.splitlines() if line.strip()]

        return folders

    except subprocess.CalledProcessError as err:
        print(f"Error: {err}")
        return []


def get_subfolders(path: str) -> List[str]:
    """Get subfolders given full path to file

    Parameters
    ----------
    path : str
        Full path to file

    Returns
    -------
    List[str]
        List of subfolders leading to path
    """
    parts = path.split(os.sep)

    # Initialize an empty list to hold subfolder paths
    subfolders = []

    # Build subfolder paths iteratively
    for i in range(1, len(parts) + 1):
        subfolder = os.sep.join(parts[:i])
        subfolders.append(subfolder)

    return subfolders


def main():
    """
    MAIN
    """

    args = config_cli()

    watch_files = args.watch_files
    os.chdir(args.watch_path)

    if args.file:
        if not os.path.exists(args.file):
            sys.exit(-1)

        with open(args.file, "r", encoding="utf-8") as watch:
            extra_files = watch.readlines()
            watch_files.extend(extra_files)

    touched_folders = get_changed_folders()

    for folder in touched_folders:
        ans = get_subfolders(folder)
        for watch in watch_files:
            # print(watch.strip().strip(os.sep))
            if watch.strip().strip(os.sep) in ans:
                print("Watched files found in touched files!")
                sys.exit(1)
    print("No files changed")
    sys.exit(0)


if __name__ == "__main__":
    main()
