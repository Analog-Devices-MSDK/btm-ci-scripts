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
per_heatmap.py

Description: CI Oriented PER Heatmap Test

"""

import argparse
import json
import os
import subprocess
import sys

RESOURCE_SHARE_DIR = os.environ.get("RESOURCE_SHARE_DIR")
if RESOURCE_SHARE_DIR is None:
    print("Cannot find resource share directory in environment!")
    sys.exit(-1)

sys.path.append(RESOURCE_SHARE_DIR)

sys.path.append("/home/btm-ci/Tools/msdk-ble-test-suite/src")

#pylint: disable=import-error,wrong-import-position
from ble_test_suite_v2.controllers import RxSensitivityTestController
from ble_test_suite_v2.phy import rx_sensitivity as rx_sens
from Resource_Share.resource_manager import ResourceManager

#pylint: enable=import-error,wrong-import-position


def flash_board(msdk: str, project: str, board_id: str) -> int:
    """Flash board

    Parameters
    ----------
    msdk : str
        path to msdk
    project : str
        name of project
    board_id : str
        id of board to flash

    Returns
    -------
    int
        return code of build and flash process
    """
    resource_manager = ResourceManager()
    target = resource_manager.get_item_value(f"{board_id}.target")
    board = resource_manager.get_item_value(f"{board_id}.board")
    build_path = os.path.join(msdk, "Examples", target, "Bluetooth", project)

    with subprocess.Popen(
        ["make", f"MAXIM_PATH={msdk}", "distclean"], cwd=build_path
    ) as proc:
        if proc.wait() != 0:
            print("!! ERROR CLEANING DIRECTORY, ABORTING !!")
            return -1

    with subprocess.Popen(
        ["make", "-j8", f"MAXIM_PATH={msdk}", f"TARGET={target}", f"BOARD={board}"],
        cwd=build_path,
    ) as proc:
        if proc.wait() != 0:
            print("!! ERROR BUILDING PROJECT, ABORTING !!")
            return -1

    elf_path = os.path.join(build_path, "build", f"{target.lower()}.elf")
    with subprocess.Popen(["bash", "-c", f"ocdflash {board_id} {elf_path}"]) as proc:
        if proc.wait() != 0:
            print("!! ERROR FLASHING, ERASING AND RETRYING 1 TIME !!")

    with subprocess.Popen(["bash", "-c", f"ocderase {board_id}"]) as proc:
        if proc.wait() != 0:
            print("!! MASS ERASE FAILED, ABORTING !!")
            return -1
    with subprocess.Popen(["bash", "-c", f"ocdflash {board_id} {elf_path}"]) as proc:
        if proc.wait() != 0:
            print("!! ERROR FLASHING, ABORTING !!")
            return -1

    return 0


def main():
    description = "Generate PER heatmaps"
    parser = argparse.ArgumentParser(
        description=description, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("msdk", type=str, help="MSDK path.")
    parser.add_argument("dut_target", type=str, help="DUT board type.")
    parser.add_argument("master_target", type=str, help="Master board type.")
    parser.add_argument("group", type=str, help="DUT/master group field.")
    parser.add_argument("results_dir", type=str, help="Base results path.")
    parser.add_argument(
        "--long",
        action="store_true",
        help="Run full sweep. Default is to run a spot check.",
    )

    args = parser.parse_args()
    if args.long:
        # cfg_path = os.environ.get("PER_CFG_FULLSWEEP")
        cfg_path = "rx_sensitivity_config.json"
    else:
        # cfg_path = os.environ.get("PER_CFG_SPOTCHECK")
        cfg_path = "rx_sensitivity_config.json"
    group = args.group.upper()
    dut_target = args.dut_target.upper()
    master_target = args.master_target.upper()
    resource_manager = ResourceManager()
    dut = resource_manager.get_applicable_items(target=dut_target, group=group)[0]
    master = resource_manager.get_applicable_items(target=master_target, group=group)[0]
    resource_manager.lock_resources([dut, master])
    print(dut)
    print(master)

    with open(cfg_path, "r", encoding="utf-8") as cfile:
        cfg = json.load(cfile)
        cfg["config"]["equipment"] = {
            "dut": dut_target,
            "dut_port": resource_manager.get_item_value(f"{dut}.hci_port"),
            "master": master_target,
            "master_port": resource_manager.get_item_value(f"{master}.hci_port"),
        }
        cfg["config"]["paths"]["results_dir"] = os.path.join(
            args.results_dir, f"{dut_target.upper()}"
        )

    with open(cfg_path, "w", encoding="utf-8") as cfile:
        cfile.write(json.dumps(cfg, indent=4))

    if flash_board(args.msdk, "BLE5_ctr", dut) != 0:
        resource_manager.unlock_resources([dut, master])
        sys.exit(-1)

    ctrl = RxSensitivityTestController(rx_sens.init_from_json(cfg_path))
    ctrl.run_test()
    passes = ctrl.results()

    if not passes:
        print("!! DUT FAILED ON ONE OR MORE SWEEPS !!")
        resource_manager.unlock_resources([dut, master])
        sys.exit(-1)

    resource_manager.unlock_resources([dut, master])
    sys.exit(0)


if __name__ == "__main__":
    main()
