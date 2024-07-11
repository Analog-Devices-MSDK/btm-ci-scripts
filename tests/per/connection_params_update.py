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


import os
import sys
import time
from typing import Dict

import matplotlib.pyplot as plt
import pandas as pd
from ble_test_suite.equipment import mc_rcdat_6000, mc_rf_sw
from ble_test_suite.results import Mask, Plot
from ble_test_suite.utils.log_util import get_formatted_logger

# pylint: disable=import-error,wrong-import-position
from max_ble_hci import BleHci
from max_ble_hci.hci_packets import EventPacket
from max_ble_hci.packet_codes import EventCode
from resource_manager import ResourceManager
from serial import Timeout

# pylint: enable=import-error,wrong-import-position





def save_results(slave, master, results: Dict[str, list], phy: str, directory):
    """Store PER Results

    Parameters
    ----------
    results : Dict[str,list]
        Results from per sweep
    """
    # print(results)
    if not os.path.exists(directory):
        os.mkdir(directory)

    df = pd.DataFrame(results)
    plot_title = f"connection_per_{slave}_{master}_{phy}"

    df.to_csv(f"{directory}/{plot_title}.csv", index=False)

    fail_bar = [30] * len(results["attens"])

    plt.plot(df["attens"], df["slave"], label=f"{slave}")
    plt.plot(df["attens"], df["master"], label=f"{master}")
    plt.plot(df["attens"], fail_bar)

    plt.title(plot_title)
    plt.xlabel(f"Received Power (dBm)")
    plt.ylabel(f"PER %")
    plt.legend()

    plt.savefig(f"{directory}/{plot_title}.png")


def print_test_config(slave, master):
    print("Using:")
    print(f"\tSlave - {slave}")
    print(f"\tMaster - {master}\n")


reconnect = False


def hci_callback(packet):
    if not isinstance(packet, EventPacket):
        print(packet)
        return

    global reconnect

    event: EventPacket = packet
    if event.evt_code == EventCode.DICON_COMPLETE:
        reconnect = True


def main():
    global reconnect
    # pylint: disable=too-many-locals
    """MAIN"""

    if len(sys.argv) < 3:
        print(f"Expected 2 inputs. Got {len(sys.argv)}")
        print("usage: <MASTER_BAORD> <SLAVE_BOARD> <RESULTS DIRECTORY")
        sys.exit(-1)

    master_board = sys.argv[1]
    slave_board = sys.argv[2]
    results_dir = sys.argv[3]

    print_test_config(slave_board, master_board)

    assert (
        master_board != slave_board
    ), f"Master must not be the same as slave, {master_board} = {slave_board}"

    resource_manager = ResourceManager()


    # config_switches(resource_manager, slave_board, master_board)

    master_hci_port = resource_manager.get_item_value(f"{master_board}.hci_port")
    slave_hci_port = resource_manager.get_item_value(f"{slave_board}.hci_port")


    master = BleHci(
        master_hci_port,
        async_callback=hci_callback,
        evt_callback=hci_callback,
        id_tag="master",
    )
    slave = BleHci(
        slave_hci_port,
        async_callback=hci_callback,
        evt_callback=hci_callback,
        id_tag="slave",
    )
    atten = mc_rcdat_6000.RCDAT6000()

    master_addr = 0x001234887733
    slave_addr = 0x111234887733

    slave.reset()
    master.reset()
    master.set_adv_tx_power(0)
    slave.set_adv_tx_power(0)
    slave.set_address(slave_addr)
    master.set_address(master_addr)

    slave.start_advertising(connect=True)
    master.init_connection(addr=slave_addr)

    print("Sleeping for initial connection")
    time.sleep(3)


    slave.update_

    attens = list(range(20, 100, 2))

    results = {"attens": [], "slave": [], "master": []}
    failed_per = False
    total_dropped_connections = 0

    prev_rx = 100000
    retries = 3

    while attens:
        i = attens[0]
        if prev_rx == i:
            retries -= 1

        print(f"RX Power {-i} dBm")
        calibrated_value = int(i + loss)

        atten.set_attenuation(calibrated_value)

        time.sleep(1)

        try:
            slave_stats, _ = slave.get_conn_stats()
            master_stats, _ = master.get_conn_stats()
        except TimeoutError:
            break

        if slave_stats.rx_data and master_stats.rx_data:
            retries = 3
            slave_per = slave_stats.per()
            master_per = master_stats.per()

            print("Slave - ", slave_per)
            print("Master - ", master_per)

            results["slave"].append(slave_per)
            results["master"].append(master_per)
            results["attens"].append(-i)
            attens.pop(0)

            if (slave_per >= 30 or master_per >= 30) and i < 70:
                failed_per = True
                print(f"Connection Failed PER TEST at {i}")
                print(f"Master: {master_per}, Slave: {slave_per}")

        elif reconnect:
            print("Attempting reconnect!")
            total_dropped_connections += 1
            reconnect = False
            slave.start_advertising(connect=True)
            master.init_connection(addr=slave_addr)
            time.sleep(2)

        prev_rx = i
        if retries == 0:
            break

        slave.reset_connection_stats()
        master.reset_connection_stats()
    try:
        master.disconnect()
        slave.disconnect()

        master.reset()
        slave.reset()
    except TimeoutError:
        pass

    save_results(slave_board, master_board, results, "1M", results_dir)

    print(f"Total Dropped Connections: {total_dropped_connections}")

    if failed_per:
        sys.exit(-1)


if __name__ == "__main__":
    main()
