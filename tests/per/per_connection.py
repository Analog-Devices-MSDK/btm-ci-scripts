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
connection.py

Description: Simple example showing creation of a connection and getting packet error metrics

"""

import sys
import time
from typing import Dict

import pandas as pd

# pylint: disable=import-error,wrong-import-position
from ble_hci import BleHci
from ble_test_suite.equipment import mc_rcdat_6000, mc_rf_sw

sys.path.append("../..")

from Resource_Share.resource_manager import ResourceManager

# pylint: enable=import-error,wrong-import-position


def config_switches(resource_manager: ResourceManager, slave: str, master: str):
    """Configure RF switches to connect DUTS

    Parameters
    ----------
    resource_manager : ResourceManager
        resource manager to access switch information
    slave : str
        slave resource
    master : str
        slave_resource
    """
    slave_sw_model, slave_sw_port = resource_manager.get_switch_config(slave)
    master_sw_model, master_sw_port = resource_manager.get_switch_config(master)

    assert (
        slave_sw_model and slave_sw_port
    ), "Slave must have the sw_model and sw_state attribute"
    assert (
        master_sw_model and master_sw_port
    ), "Master must have the sw_model and sw_state attribute"
    assert (
        slave_sw_model != master_sw_model
    ), "Boards must be on opposite switches to connect!"

    rf_sw_slave = mc_rf_sw.MiniCircuitsRFSwitch(model=slave_sw_model)
    rf_sw_master = mc_rf_sw.MiniCircuitsRFSwitch(model=master_sw_model)
    rf_sw_slave.set_sw_state(slave_sw_port)
    rf_sw_master.set_sw_state(master_sw_port)


def save_results(results: Dict[str, list]):
    """Store PER Results

    Parameters
    ----------
    results : Dict[str,list]
        Results from per sweep
    """
    data = pd.DataFrame(results)
    data.to_csv("connection_per.csv", index=False)


def main():
    # pylint: disable=too-many-locals
    """MAIN"""

    if len(sys.argv) < 4:
        print(f"Expected 2 inputs. Got {len(sys.argv)}")
        print("usage: <MASTER_BAORD> <SLAVE_BOARD>")
        sys.exit(-1)

    master_board = sys.argv[1]
    slave_board = sys.argv[2]

    assert (
        master_board != slave_board
    ), f"Master must not be the same as slave, {master_board} = {slave_board}"

    resource_manager = ResourceManager()

    config_switches(resource_manager, slave_board, master_board)

    master_hci_port = resource_manager.get_item_value(f"{master_board}.hci_port")
    slave_hci_port = resource_manager.get_item_value(f"{slave_board}.hci_port")

    master = BleHci(master_hci_port)
    slave = BleHci(slave_hci_port)
    atten = mc_rcdat_6000.RCDAT6000()

    master_addr = 0x001234887733
    slave_addr = 0x111234887733

    master.reset()
    slave.reset()
    master.set_adv_tx_power(0)
    slave.set_adv_tx_power(0)
    slave.set_address(slave_addr)
    master.set_address(master_addr)

    slave.start_advertising(connect=True)
    master.init_connection(addr=slave_addr)

    attens = list(range(20, 100, 5))

    results = {"attens": attens, "slave": [], "master": []}

    for i in attens:
        atten.set_attenuation(i)
        time.sleep(10)

        slave_stats, _ = slave.get_conn_stats()
        master_stats, _ = master.get_conn_stats()

        if slave_stats.rx_data and master_stats.rx_data:
            slave_per = slave_stats.per()
            master_per = master_stats.per()

            results["slave"].append(slave_per)
            results["master"].append(master_per)

            if (slave_per >= 30 or master_per >= 30) and i < 70:
                save_results(results)
                print(f"Connection Failed PER TEST at {i}")
                print(f"Master: {master_per}, Slave: {slave_per}")
                sys.exit(-1)

        slave.reset_connection_stats()
        master.reset_connection_stats()

    master.disconnect()
    slave.disconnect()

    master.reset()
    slave.reset()

    save_results(results)
