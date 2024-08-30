#! /usr/bin/env python3
###############################################################################
#
#
# Copyright (C) 2023 Maxim Integrated Products, Inc., All Rights Reserved.
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
##############################################################################
#
# Copyright 2023 Analog Devices, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
##############################################################################
"""
ocdflash.py

Description: ocdflash cli

"""
import argparse

# pylint: disable=redefined-builtin,import-error
import os
import socket
import sys
from pathlib import Path

from rich import print
from rich.prompt import Prompt

from resource_manager import ResourceManager

# pylint: enable=redefined-builtin,import-error


def is_elf(file_path):
    """Check if a file is an ELF file by reading its magic number."""
    try:
        with open(file_path, "rb") as file:
            magic = file.read(4)
            return magic == b"\x7fELF"
    except IOError:
        print(f"Error reading {file_path}")
        return False


def find_elf_files(directory="."):
    """Find ELF files in the current directory and one level below using pathlib."""
    elf_files = []

    current_dir = Path(directory)

    for file in current_dir.iterdir():
        if file.is_file() and is_elf(file):
            elf_files.append(str(file))

    for file in current_dir.glob("*/*"):
        if file.is_file() and is_elf(file):
            elf_files.append(str(file))

    return elf_files


def main():
    """MAIN"""
    parser = argparse.ArgumentParser()

    parser.add_argument("resource", help="Resource name as listed in board config")

    parser.add_argument(
        "elf", default="", nargs="?", help="echo the string you use here"
    )
    parser.add_argument("owner", default="", nargs="?", help="Owner of resource")

    args = parser.parse_args()

    resource_manager = ResourceManager()

    resource = args.resource
    elf = args.elf
    owner = args.owner

    if elf == "":
        target_str = resource_manager.get_target(resource).lower()
        elf = f"build/{target_str}.elf"

    # Probably a better way.
    # This will block workflows if the path is messed up. So just bypass feature on CI machine
    hostname = socket.gethostname()
    if hostname != "wall-e" and not os.path.exists(elf):
        elf = ""
        elf_files = find_elf_files()
        for file in elf_files:
            this_elf = Prompt.ask(f"Is this the file {file} (y/n)?", default="y")
            if this_elf in ("y", "Y"):
                elf = file
                break

    if not os.path.exists(elf):
        print("[red]No elf file given and could not be determined![/red]")
        sys.exit(-1)

    resource_manager.resource_flash(resource_name=resource, elf_file=elf, owner=owner)


if __name__ == "__main__":
    main()
