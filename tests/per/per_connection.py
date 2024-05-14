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

import time
import sys
from ble_hci import BleHci
from ble_test_suite.equipment import mc_rf_sw , mc_rcdat_6000

sys.path.append("../..")

# pylint: disable=import-error,wrong-import-position
from Resource_Share.resource_manager import ResourceManager

# pylint: enable=import-error,wrong-import-position
def config_switches(resource_manager:ResourceManager, slave, master):
    slave_sw_model, slave_sw_port = resource_manager.get_switch_config(slave)
    master_sw_model, master_sw_port = resource_manager.get_switch_config(master)

    assert slave_sw_model != master_sw_model, f'Boards must be on opposite switches to connect!'

    rf_sw_slave = mc_rf_sw.MiniCircuitsRFSwitch(model=slave_sw_model)
    rf_sw_master = mc_rf_sw.MiniCircuitsRFSwitch(model=master_sw_model)
    rf_sw_slave.set_sw_state(slave_sw_port)
    rf_sw_master.set_sw_state(master_sw_port)


def main():
    """MAIN"""

    if len(sys.argv) < 4:
        print(f"Expected 2 inputs. Got {len(sys.argv)}")
        print("usage: <MASTER_BAORD> <SLAVE_BOARD>")
        sys.exit(-1)

    MASTER_BOARD = sys.argv[1]
    SLAVE_BOARD = sys.argv[2]
    
    assert MASTER_BOARD != SLAVE_BOARD, f'Master must not be the same as slave, {MASTER_BOARD} = {SLAVE_BOARD}'
    
    resource_manager = ResourceManager()
    
    MASTER_HCI_PORT = resource_manager.get_item_value(f'{MASTER_BOARD}.hci_port')
    SLAVE_HCI_PORT = resource_manager.get_item_value(f'{SLAVE_BOARD}.hci_port')
    

    config_switches(resource_manager, SLAVE_BOARD, MASTER_BOARD)


    master = BleHci(MASTER_HCI_PORT)
    slave = BleHci(SLAVE_HCI_PORT)





    master.reset()
    slave.reset()

    master_addr = 0x001234887733
    slave_addr = 0x111234887733

    master.set_adv_tx_power(-10)
    slave.set_adv_tx_power(-10)

    slave.set_address(slave_addr)
    master.set_address(master_addr)

    slave.start_advertising(connect=True)
    master.init_connection(addr=slave_addr)

    while True:
        slave_stats, _ = slave.get_conn_stats()
        master_stats, _ = master.get_conn_stats()

        if slave_stats.rx_data and master_stats.rx_data:
            print(f"Slave PER {slave_stats.per()}")
            print(f"Master PER {master_stats.per()}")
            break

        time.sleep(0.5)

    master.disconnect()
    slave.disconnect()

    master.reset()
    slave.reset()
