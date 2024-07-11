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
import shutil
import time
import argparse
import matplotlib.pyplot as plt
from rich import print
from alive_progress import alive_bar
from glob import glob

# pylint: disable=import-error,wrong-import-position
from max_ble_hci import BleHci
from max_ble_hci.data_params import DataPktStats
from max_ble_hci.hci_packets import EventPacket
from max_ble_hci.packet_codes import EventCode
from resource_manager import ResourceManager
from ble_test_suite.results.report_generator import ReportGenerator

# pylint: enable=import-error,wrong-import-position


def save_per_plot(slave, master, sample_rate, directory):
    time_data = [x * sample_rate for x in range(len(slave))]

    pers_slave = []
    pers_master = []


    stat: DataPktStats

    for i, stat in enumerate(slave):
        try:
            pers_slave.append(stat.per())
            pers_master.append(master[i].per())
        except ZeroDivisionError:
            print('ZERO DIV')
            pers_slave.append(100)
            pers_master.append(100)

    

    filepath = f"{directory}/per.png"
    
    plt.plot(time_data, pers_slave, label="slave")
    plt.plot(time_data, pers_master, label="master")
    plt.ylim([0, 100])
    plt.xlabel("time (sec)")
    plt.ylabel("PER (%)")
    plt.title("PER Vs. Time")
    plt.legend()
    plt.savefig(filepath)
    plt.close()

    return filepath

def save_individual(data, sample_rate, label, directory) -> DataPktStats:
    time_data = [x * sample_rate for x in range(len(data))]

    crcs = []
    timeouts = []
    rx_ok = []
    tx_data = []
    rx_setup = []
    tx_setup = []
    rx_isr = []
    tx_isr = []

    stat: DataPktStats

    for stat in data:
        rx_ok.append(stat.rx_data)
        crcs.append(stat.rx_data_crc)
        timeouts.append(stat.rx_data_timeout)
        tx_data.append(stat.tx_data)

        rx_setup.append(stat.rx_setup)
        tx_setup.append(stat.tx_setup)
        rx_isr.append(stat.rx_isr)
        tx_isr.append(stat.tx_isr)

    # RX Packet stats
    plt.plot(time_data, rx_ok, label="RX-OK")
    plt.plot(time_data, crcs, label="RX-CRC")
    plt.plot(time_data, timeouts, label="RX-Timeout")
    plt.xlabel("time (sec)")
    plt.ylabel("Packets (count)")
    plt.title(f"{label} RX Packet Stats")
    plt.legend()
    plt.savefig(f"{directory}/{label}_rx_data.png")
    plt.close()

    # TX Packet Stats
    plt.plot(time_data, tx_data)
    plt.xlabel("time (sec)")
    plt.ylabel("Packets (count)")
    plt.title(f"{label} Transmitted Packets Vs. Time")
    plt.savefig(f"{directory}/{label}_tx_data.png")
    plt.close()

    # ISR Timing
    plt.plot(time_data, tx_isr, label="TX-ISR")
    plt.plot(time_data, rx_isr, label="RX-ISR")
    plt.xlabel("time (sec)")
    plt.ylabel("ISR Times (usec)")
    plt.title(f"{label} ISR Timing Vs. Time")
    plt.legend()
    plt.savefig(f"{directory}/{label}_isr.png")
    plt.close()

    # Setup Timing
    plt.plot(time_data, tx_setup, label="TX-Setup")
    plt.plot(time_data, rx_setup, label="RX-Setup")
    plt.xlabel("time (sec)")
    plt.ylabel("SetupTimes (usec)")
    plt.title(f"{label} Setup Timing Vs. Time")
    plt.legend()
    plt.savefig(f"{directory}/{label}_setup.png")
    plt.close()


def make_table(data: DataPktStats):
    table = [["Stat", "Value"]]

    for key, value in data.__dict__.items():
        if isinstance(value, float):
            table.append([key, round(value, 2)])
        else:
            table.append([key, value])

    table.append(["PER", data.per()])

    return table


def add_pdf(slave_overall, master_overall, directory, dropped_connections):
    charts = glob(f"{directory}/*.png")

    #make sure to add this as the first image
    perchart = f'{directory}/per.png'
    gen.add_image(perchart, img_dims=(8 * inch, 6 * inch))
    
    
    charts.remove(perchart)
    gen = ReportGenerator(f"{directory}/connection_stability_report.pdf")
    inch = gen.rlib.units.inch
    for chart in charts:
        gen.add_image(chart, img_dims=(8 * inch, 6 * inch))

    slave_table = make_table(slave_overall)
    master_table = make_table(master_overall)

    gen.new_page()
    gen.add_table(
        slave_table, col_widths=(gen.page_width - inch) / 2, caption="Slave Metrics"
    )
    gen.add_table(
        master_table, col_widths=(gen.page_width - inch) / 2, caption="Master Metrics"
    )

    misc_table = [
        ['Dropped Connections', dropped_connections]
    ]
    gen.add_table(
        misc_table, col_widths=(gen.page_width - inch) / 2, caption="Master Metrics"
    )

    gen.build(doc_title="Connection Stability Report")


def save_results(
    slave, master, sample_rate, dropped_connections: int, phy: str, directory: str
):
    """Store PER Results

    Parameters
    ----------
    results : Dict[str,list]
        Results from per sweep
    """
    
    if not os.path.exists(directory):
        os.mkdir(directory)
    else:
        shutil.rmtree(directory)
        os.mkdir(directory)

    save_per_plot(slave, master, sample_rate=sample_rate, directory=directory)

    save_individual(
        data=slave, sample_rate=sample_rate, label=f"slave_{phy}", directory=directory
    )
    save_individual(
        data=master, sample_rate=sample_rate, label=f"master_{phy}", directory=directory
    )



    add_pdf(slave[-1], master[-1], directory, dropped_connections )


reconnect = False


def hci_callback(packet):
    if not isinstance(packet, EventPacket):
        print(packet)
        return

    global reconnect

    event: EventPacket = packet
    if event.evt_code == EventCode.DICON_COMPLETE:
        reconnect = True


def config_cli():
    parser = argparse.ArgumentParser(
        description="Evaluates connection perfomrance and stability over a long period of time",
    )

    parser.add_argument("master", help="Master board")
    parser.add_argument("slave", help="Slave Board")
    parser.add_argument("-r", "--results", help="Results directory")
    parser.add_argument(
        "-p", "--phy", default="1M", help="Connection PHY (1M, 2M, S2, S8)"
    )
    parser.add_argument("-t", "--time", default=1800, help="Test time")
    parser.add_argument(
        "-d", "--directory", default="stability_results", help="Result Directory"
    )

    parser.add_argument(
        "-s",
        "--sample-rate",
        default=1,
        help="Sample rate in seconds. Minimum of 1 second",
    )

    return parser.parse_args()


def main():
    global reconnect
    # pylint: disable=too-many-locals
    """MAIN"""

    args = config_cli()

    master_board: str = args.master
    slave_board: str = args.slave

    assert (
        master_board != slave_board
    ), f"Master must not be the same as slave, {master_board} = {slave_board}"

    resource_manager = ResourceManager()

    sample_rate = args.sample_rate if args.sample_rate >= 1 else 1
    iterations = int(int(args.time) / float(sample_rate))
    assert isinstance(iterations, int)

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
    time.sleep(4)

    slave_cummulative = []
    master_cummulative = []
    total_dropped_connections = 0

    with alive_bar(iterations) as bar:
        for _ in range(iterations):
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

            # slave.reset_connection_stats()
            # master.reset_connection_stats()

            bar()
            time.sleep(sample_rate)

    try:
        slave_stats, _ = slave.get_conn_stats()
        master_stats, _ = master.get_conn_stats()
        slave_cummulative.append(slave_stats)
        master_cummulative.append(master_stats)
        master.disconnect()
        slave.disconnect()
        master.reset()
        slave.reset()
    except TimeoutError:
        pass

    print("[cyan]Plotting results. This may take some time[/cyan]")
    save_results(
        slave=slave_cummulative,
        master=master_cummulative,
        dropped_connections=total_dropped_connections,
        phy=args.phy,
        sample_rate=sample_rate,
        directory=args.directory,
    )


if __name__ == "__main__":
    main()
