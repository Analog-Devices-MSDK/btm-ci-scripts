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
from typing import Dict, List
import argparse
import matplotlib.pyplot as plt
import pandas as pd
from ble_test_suite.equipment import mc_rcdat_6000, mc_rf_sw
from ble_test_suite.results import Mask, Plot
from ble_test_suite.utils.log_util import get_formatted_logger
from alive_progress import alive_bar

# pylint: disable=import-error,wrong-import-position
from max_ble_hci import BleHci
from max_ble_hci.data_params import DataPktStats
from max_ble_hci.hci_packets import EventPacket
from max_ble_hci.packet_codes import EventCode
from resource_manager import ResourceManager
from serial import Timeout

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

    with mc_rf_sw.MiniCircuitsRFSwitch(model=slave_sw_model) as sw_slave:
        print("Configuring Slave Switch")
        sw_slave.set_sw_state(slave_sw_port)

    with mc_rf_sw.MiniCircuitsRFSwitch(model=master_sw_model) as sw_master:
        print("Configuring Master Switch")
        sw_master.set_sw_state(master_sw_port)



def save_individual(data, sample_rate, label, directory) -> DataPktStats:
    
    time = [x * sample_rate for x in range(len(data))]

    pers = []
    crcs = []
    timeouts = []
    rx_ok = []
    tx_data = []
    rx_setup = []
    tx_setup = []
    rx_isr = []
    tx_isr = []

    stat: DataPktStats
    cummulative_stats  = DataPktStats()

    
    for stat in data:
        try:
            pers.append(stat.per())
        except ZeroDivisionError:
            pers.append(100)

        rx_ok.append(stat.rx_data)
        crcs.append(stat.rx_data_crc)
        timeouts.append(stat.rx_data_timeout)
        tx_data.append(stat.tx_data)

        rx_setup.append(stat.rx_setup)
        tx_setup.append(stat.tx_setup)
        rx_isr.append(stat.rx_isr)
        tx_isr.append(stat.tx_isr)

        cummulative_stats.rx_data += stat.rx_data
        cummulative_stats.rx_data_crc += stat.rx_data_crc
        cummulative_stats.rx_data_timeout += stat.rx_data_timeout
        cummulative_stats.tx_data += stat.tx_data
        cummulative_stats.err_data += stat.err_data

        ## SUM for average
        cummulative_stats.rx_isr += stat.rx_isr
        cummulative_stats.tx_isr += stat.tx_isr
        cummulative_stats.rx_setup += stat.rx_setup
        cummulative_stats.tx_setup += stat.tx_setup


    # General PER
    plt.plot(time, pers)
    plt.xlabel('time (sec)')
    plt.ylabel('PER (%)')
    plt.title('PER Vs. Time')
    plt.savefig(f'{directory}/{label}_per.png')
    plt.close()

    # RX Packet stats
    plt.plot(time, rx_ok, label='RX-OK')
    plt.plot(time, crcs, label='RX-CRC')
    plt.plot(time, timeouts, label='RX-Timeout')
    plt.xlabel('time (sec)')
    plt.ylabel('Packets (count)')
    plt.title('RX Packet Stats')
    plt.legend()
    plt.savefig(f'{directory}/{label}_rx_data.png')
    plt.close()


    # TX Packet Stats
    plt.plot(time, tx_data)
    plt.xlabel('time (sec)')
    plt.ylabel('Packets (count)')
    plt.title('Transmitted Packets Vs. Time')
    plt.savefig(f'{directory}/{label}_tx_data.png')
    plt.close()

    # ISR Timing
    plt.plot(time, tx_isr, label='TX-ISR')
    plt.plot(time, rx_isr, label='RX-ISR')
    plt.xlabel('time (sec)')
    plt.ylabel('ISR Times (s)')
    plt.title('ISR Timing Vs. Time')
    plt.savefig(f'{directory}/{label}_isr.png')
    plt.close()

    # Setup Timing
    plt.plot(time, tx_setup, label='TX-Setup')
    plt.plot(time, rx_setup, label='RX-Setup')
    plt.xlabel('time (sec)')
    plt.ylabel('ISR Times (s)')
    plt.title('ISR Timing Vs. Time')
    plt.savefig(f'{directory}/{label}_setup.png')
    plt.close()


    cummulative_stats.rx_isr /= len(data)
    cummulative_stats.tx_isr /= len(data)
    cummulative_stats.rx_setup /= len(data)
    cummulative_stats.tx_setup /= len(data)


    return cummulative_stats
    





    
    

def save_results(slave:List[Dict[str:int]], master:List[Dict[str:int]], sample_rate, dropped_connections:int, phy: str, directory:str):
    """Store PER Results

    Parameters
    ----------
    results : Dict[str,list]
        Results from per sweep
    """

    if not os.path.exists(directory):
        os.mkdir(directory)



    slave_overall = save_individual(data=slave, sample_rate=sample_rate, label = f'slave_{phy}', directory=directory)
    master_overall = save_individual(data=master, sample_rate=sample_rate, label = f'master_{phy}', directory=directory)



    with open(f'{directory}/cummulative.txt', 'w') as stats_file:
            stats_text = ['RX Overall\n----------------------\n']
        
            for key, value in slave_overall.__dict__.items():
                stats_text.append(f'{key}:{value}')

            stats_text.append('TX Overall\n----------------------\n')
            for key, value in master_overall.__dict__.items():
                stats_text.append(f'{key}:{value}')


            stats_text.append(f'Dropped connections: {dropped_connections}')
            stats_file.writelines(stats_text)




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


def config_cli(self):
    parser = argparse.ArgumentParser(
                    prog='ProgramName',
                    description='Evaluates connection perfomrance and stability over a long period of time',
                    )
    
    parser.add_argument('master', help='Master board')
    parser.add_argument('slave', help='Slave Board')
    parser.add_argument('-r', "--results", help='Results directory')
    parser.add_argument('-p', "--phy", default='1M', help='Connection PHY (1M, 2M, S2, S8)')
    parser.add_argument('-d', "--duration",default=1800,help='Results directory')
    parser.add_argument('-s', "--sample-rare", default=3,help='Sample rate in seconds. Minimum of 1 second')



    return parser.parse_args()



def main():
    global reconnect
    # pylint: disable=too-many-locals
    """MAIN"""

    args = config_cli()

    master_board: str = args.master
    slave_board: str = args.slave

    print_test_config(slave = slave_board, master=master_board)

    

    assert (
        master_board != slave_board
    ), f"Master must not be the same as slave, {master_board} = {slave_board}"

    resource_manager = ResourceManager()

    try:
        loss = resource_manager.get_item_value("rf_bench.cal.losses.2440")
        loss = float(loss)
    except KeyError:
        print("Could not find cal data in config. Defaulting to 0")
        loss = 0.0


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



    slave_cummulative = []
    master_cummulative = []
    total_dropped_connections = 0

    sample_rate = args.sample_rate if sample_rate >= 1 else 1

    iterations = args.sample_rate * args.duration

    with alive_bar(iterations) as bar:

        for i in range(iterations):
            time.sleep(args.sample_rate)
            try:
                slave_stats, _ = slave.get_conn_stats()
                master_stats, _ = master.get_conn_stats()
                slave_cummulative.append(slave_stats)
                master_cummulative.append(master_stats)
            except TimeoutError:
                break

            
            if reconnect:
                total_dropped_connections += 1
                reconnect = False
                slave.start_advertising(connect=True)
                master.init_connection(addr=slave_addr)
                time.sleep(2)

            
            slave.reset_connection_stats()
            master.reset_connection_stats()

            bar()    
            
        try:
            master.disconnect()
            slave.disconnect()

            master.reset()
            slave.reset()
        except TimeoutError:
            pass
        



    save_results(slave_cummulative, master_cummulative, total_dropped_connections, args.phy, args.directory)




if __name__ == "__main__":
    main()
