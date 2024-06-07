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
# trademarks, maskwork rights, or any other form of intellectual# property whatsoever. Maxim Integrated Products, Inc. retains all
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
import logging
import os
import sys
from typing import Tuple

from ble_test_suite.controllers import RxSensitivityTestController
from ble_test_suite.equipment.mc_rf_sw import MiniCircuitsRFSwitch
from ble_test_suite.phy import rx_sensitivity as RxSens
from resource_manager import ResourceManager

ENV_CI_CONFIG = "CI_CONFIG_DIR"
CALIBRATION_FNAME = "rfphy_sw2atten_calibration.json"
TEST_MASTER_ID = "nRF52840_1"
DESC = """
Run a Direct-Test Mode Packet Error Rate
spot-check for the specified DUT on the
indicated LE PHY. Master device is always
the NRF52840 board.
"""


def _setup_ci():
    parser = argparse.ArgumentParser(
        description=DESC, formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("master", type=str, help="Desired master board config ID.")
    parser.add_argument("dut", type=str, help="Desired DUT board config ID.")
    parser.add_argument(
        "--phy", type=str, default="1M", choices=["1M", "2M", "S2", "S8"]
    )
    parser.add_argument("--channels", type=str, default="0,19,39")
    parser.add_argument("--attenuation-step", type=str, default="2")

    parser.add_argument(
        "--results", type=str, default="results", help="Results directory."
    )
    parser.add_argument("--num-packets", type=int, default=1000, help="Num packets.")

    return parser.parse_args()


def cfg_switches(rm: ResourceManager, devs: Tuple[str, str]) -> None:
    """Configure the RF switches to connect master to DUT.

    Parameters
    ----------
    rm : ResourceManager
        Resource manager object.
    devs : Tuple[str, str]
        Master/DUT board ID strings.

    """
    dev0_sw_model, dev0_sw_port = rm.get_switch_config(devs[0])
    dev1_sw_model, dev1_sw_port = rm.get_switch_config(devs[1])

    print(dev0_sw_model, dev1_sw_model)

    if None in [dev0_sw_model, dev0_sw_port, dev1_sw_model, dev1_sw_port]:
        raise RuntimeError("Switches must have both a model and a state attribute.")
    if dev0_sw_model == dev1_sw_model:
        raise RuntimeError("Boards are on the same switch and cannot connect.")

    with MiniCircuitsRFSwitch(model=dev0_sw_model) as rf_sw:
        rf_sw.set_sw_state(dev0_sw_port)
    with MiniCircuitsRFSwitch(model=dev1_sw_model) as rf_sw:
        rf_sw.set_sw_state(dev1_sw_port)


def create_results_dir(results_dir):
    import pathlib

    pathlib.Path(results_dir).mkdir(parents=True, exist_ok=True)

    os.mkdir


def main():
    args = _setup_ci()
    cal_file = os.path.join(os.getenv(ENV_CI_CONFIG), CALIBRATION_FNAME)
    rm = ResourceManager()

    master_info = (
        rm.get_item_value(f"{args.master}.target"),
        rm.get_item_value(f"{args.master}.hci_port"),
    )
    dut_info = (
        rm.get_item_value(f"{args.dut}.target"),
        rm.get_item_value(f"{args.dut}.hci_port"),
    )
    print(master_info)
    print(dut_info)
    cfg_switches(rm, (args.master, args.dut))

    print(args.phy)

    if args.phy in ("S2", "S8"):
        attenuation_stop = -104
    else:
        attenuation_stop = -100

    test_settings = {
        "results_dir": args.results,
        "calibration_file": cal_file,
        "num_packets": args.num_packets,
        "packet_lens": "37",
        "rx_input_powers": f"-20:{attenuation_stop}:{args.attenuation_step}",
        "phy": args.phy,
        "channels": args.channels,
        "margin": 2,
        "create_heatmap": {"per": True},
        "create_surface_plot": {"per": False},
        "create_masked_heatmap": {"per": False},
        "create_masked_surface_plot": {"per": False},
        "create_lineplot": {"per": True},
    }

    create_results_dir(args.results)

    cfg = RxSens.init_new_test(master_info, dut_info, test_setup=test_settings)
    ctrl = RxSensitivityTestController(cfg, hci_log_level=logging.WARN)

    ctrl.run_test()

    if not ctrl.results():
        sys.exit(-1)


if __name__ == "__main__":
    main()
