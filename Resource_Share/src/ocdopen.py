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
ocdopen.py

Description: ocdopen cli
"""
import argparse
import os
import subprocess

from resource_manager import ResourceManager


def main():
    """MAIN"""
    parser = argparse.ArgumentParser()
    parser.add_argument("resource", help="Resource name as listed in board config")
    args = parser.parse_args()

    resource_manager = ResourceManager()

    resource = args.resource

    ocdpath = os.getenv("OPENOCD_PATH")

    resource_manager._is_ocd_capable(resource)
    dapsn = resource_manager.get_dapsn(resource)
    gdb, telnet, tcl = resource_manager.get_ocdports(resource)
    target = resource_manager.get_target(resource)

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
    ]

    try:
        subprocess.run(command, check=False)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
