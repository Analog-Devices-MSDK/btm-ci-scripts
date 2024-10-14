###############################################################################
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
# ~/Workspace/ci_config/phy_test_cfgs/ci_cfgs/cmw/sanity_check/
"""
Script for running PHY verification tests.
"""
import argparse
import datetime
import json
import logging
import os
import sys
from typing import Tuple
from ble_test_suite.controllers import MasterController
from ble_test_suite.equipment import MiniCircuitsRFSwitch
from btm_resource_manager import ResourceManager

DEF_CFG = os.path.join(os.getenv("CI_PHYTEST_CFG_DIR"), "phyTest_master.json")

def configure_switches(rm: ResourceManager, devs: Tuple[str]) -> None:
    """Configure the RF switches to connect equipment.

    Parameters
    ----------
    rm : ResourceManager
        Resource manager object.
    devs : Tuple[str]
        Equipment ID strings.

    """
    for dev in devs:
        model, port = rm.get_switch_config(dev)
        if None in [model, port]:
            raise RuntimeError("Switches must have both a model and a state attribute.")
        with MiniCircuitsRFSwitch(model=model) as rfsw:
            rfsw.set_sw_state(port)

def get_trace_lvl(count: int) -> int:
    if count > 2:
        return logging.DEBUG
    if count > 1:
        return logging.INFO
    if count > 0:
        return logging.WARNING
    return logging.ERROR

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run PHY verification.",
        formatter_class=argparse.RawTextHelpFormatter
    )

    parser.add_argument(
        "--master",
        dest="master_id",
        type=str,
        default=None,
        help="Master device ID. Must be accessible via the ResourceManager."
    )
    parser.add_argument(
        "--dut",
        dest="dut_id",
        type=str,
        default=None,
        help="DUT device ID. Must be accessible via the ResourceManager."
    )
    parser.add_argument(
        "-f", "--cfg-file",
        dest="cfg_filepath",
        type=str,
        default=None,
        help="Top-level configuration file path. Default is CI-specific config."
    )
    parser.add_argument(
        "-d", "--cfg-dir",
        dest="cfg_directory",
        type=str,
        default=None,
        help="Test-level configuration directory path."
    )
    parser.add_argument(
        "-r", "--results",
        dest="results_dir",
        type=str,
        default=None,
        help="Results directory override."
    )
    parser.add_argument(
        "-c", "--checkpoint",
        dest="ckp_path",
        type=str,
        default=None,
        help="Run from checkpoint file at the indicated path."
    )
    parser.add_argument(
        "--repo",
        dest="git_repo",
        type=str,
        default=None,
        help="Github repo from which tests are being run"
    )
    parser.add_argument(
        "--branch",
        dest="git_branch",
        type=str,
        default=None,
        help="Github branch from which tests are being run"
    )
    parser.add_argument(
        "--commit",
        dest="git_commit",
        type=str,
        default=None,
        help="Github commit hash for which tests are being run."
    )
    parser.add_argument(
        "-v", "--verbose",
        dest="hci_trace_level",
        action="count",
        default=0,
        help="HCI verbosity. Adding 'v's increases verbosity."
    )
    parser.add_argument(
        "--no-pdf",
        dest="create_pdf",
        action="store_false",
        help="Do not generate a PDF report."
    )
    parser.add_argument(
        "--local",
        action='store_true',
        help='Set env to be local (i.e. do not configure switches)'
    )

    args = parser.parse_args()
    rm = ResourceManager()

    equipment = {}
    cfg = args.cfg_filepath
    from_ckp = False
    hci_trace_lvl = get_trace_lvl(args.hci_trace_level)
    test_conditions = {}

    if args.ckp_path is not None:
        cfg = args.ckp_path
        from_ckp = True


    if args.local and cfg is None:
        raise ValueError(
            "Top-level configuration filepath must be provided when running locally."
        )

    if args.master_id is not None:
        equipment["master"] = (
            rm.get_item_value(f"{args.master_id}.target"),
            rm.get_item_value(f"{args.master_id}.hci_port")
        )
    if args.dut_id is not None:
        equipment["dut"] = (
            rm.get_item_value(f"{args.dut_id}.target"),
            rm.get_item_value(f"{args.dut_id}.hci_port")
        )    

    if not equipment:
        equipment=None

    if not args.local and args.ckp_path is None:
        configure_switches(rm, [args.dut_id])
        if cfg is None:
            cfg = DEF_CFG
            test_conditions = {
                "dut" : rm.get_item_value(f"{args.dut_id}.target"),
                "master" : rm.get_item_value(f"{args.master_id}.target"),
                "date/time" : datetime.datetime.now().strftime('%m/%d/%y, %H:%M:%S')
            }
    
    if args.git_repo is not None and args.git_branch:
        test_conditions["git_info"] = f"{args.git_repo}/{args.git_branch}"
    elif args.git_repo is not None:
        test_conditions["repo"] = args.git_repo
    elif args.git_branch is not None:
        test_conditions["branch"] = args.git_branch
    if args.git_commit is not None:
        test_conditions["commit_hash"] = args.git_commit

    test_conditions = test_conditions or None

    if args.cfg_directory is not None and not from_ckp:
        with open(cfg, "r", encoding="utf-8") as cfile:
            cfg = json.load(cfile)
        cfg["test_config_directory"] = args.cfg_directory
        if args.results_dir is not None:
            cfg["results_directory"] = args.results_dir
        if test_conditions is not None:
            cfg["test_conditions"] = test_conditions
    elif test_conditions is not None and not from_ckp:
        with open(cfg, "r", encoding='utf-8') as cfile:
            cfg = json.load(cfile)
        cfg["test_conditions"].update(test_conditions)
    elif args.results_dir is not None and not from_ckp:
        with open(cfg, "r", encoding='utf-8') as cfile:
            cfg = json.load(cfile)
        cfg["results_directory"] = args.results_dir


    ctrl = MasterController(
        cfg,
        equipment=equipment,
        checkpoint=from_ckp,
        hci_log_level=hci_trace_lvl
    )
    ctrl.run_tests()
    passes = ctrl.results(pdf=args.create_pdf)
    if not passes:
        sys.exit(1)
