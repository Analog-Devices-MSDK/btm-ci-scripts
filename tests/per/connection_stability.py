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


import argparse
import os
import shutil
import subprocess
import time
from datetime import datetime
from glob import glob
from typing import List

import matplotlib.pyplot as plt
import resource_manager

# pylint: disable=import-error,wrong-import-position
from alive_progress import alive_bar
from ble_test_suite.results.report_generator import ReportGenerator
from max_ble_hci import BleHci
from max_ble_hci.data_params import DataPktStats
from max_ble_hci.hci_packets import EventPacket
from max_ble_hci.packet_codes import EventCode
from packaging import version
from resource_manager import ResourceManager
from rich import print

# pylint: enable=import-error,wrong-import-position

if version.parse(resource_manager.__version__) < version.parse("1.1.1"):
    raise RuntimeError("Resource manager of 1.1.1 or greater is required")


def get_git_hash(path):
    try:
        return (
            subprocess.check_output(["git", f"-C {path}" "rev-parse", "HEAD"])
            .decode("ascii")
            .strip()
        )
    except:
        return "Unknown"


def save_per_plot(periph, central, sample_rate, directory):
    time_data = [x * sample_rate for x in range(len(periph))]

    pers_periph = []
    pers_central = []

    stat: DataPktStats

    for i, stat in enumerate(periph):
        try:
            pers_periph.append(stat.per())
        except ZeroDivisionError:
            pers_periph.append(100)

        try:
            pers_central.append(central[i].per())
        except ZeroDivisionError:
            pers_central.append(100)

    filepath = f"{directory}/per.png"

    plt.plot(time_data, pers_periph, label="peripheral", linestyle="--")
    plt.plot(time_data, pers_central, label="central")
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
    return [
        ["Stat", "Value", "Unit"],
        ["RX OK", data.rx_data, "Count"],
        ["RX CRC", data.rx_data_crc, "Count"],
        ["RX Timeout", data.rx_data_timeout, "Count"],
        ["TX OK", data.tx_data, "Count"],
        ["Err Data", data.err_data, "Count"],
        ["RX Setup", data.rx_setup, "usec"],
        ["TX Setup", data.tx_setup, "usec"],
        ["RX ISR", data.rx_isr, "usec"],
        ["TX ISR", data.tx_isr, "usec"],
        ["PER", round(data.per(), 2), "%"],
    ]


def make_misc_table(misc_data: dict):
    misc_table = [["Metric", "Value"]]

    for key, value in misc_data.items():
        if isinstance(value, float):
            misc_table.append([key, round(value, 2)])
        else:
            misc_table.append([key, value])

    return misc_table


def make_version_table():
    return [
        ["Repo", "Git Hash"],
        ["MSDK", get_git_hash(os.getenv("MAXIM_PATH"))],
        ["RF-PHY", get_git_hash(os.getenv("RF_PHY_PATH"))],
    ]


def add_pdf(
    periph_overall: List[dict],
    central_overall: List[dict],
    directory: str,
    misc_data: dict,
):
    now = datetime.now()
    filepath_date = now.strftime("%m_%d_%y")
    gen = ReportGenerator(
        f"{directory}/connection_stability_report_{filepath_date}.pdf"
    )

    charts = glob(f"{directory}/*.png")

    inch = gen.rlib.units.inch

    # make sure to add this as the first image
    perchart = f"{directory}/per.png"
    gen.add_image(perchart, img_dims=(8 * inch, 6 * inch))

    charts.remove(perchart)
    for chart in charts:
        gen.add_image(chart, img_dims=(8 * inch, 6 * inch))

    gen.new_page()
    gen.add_table(
        make_table(periph_overall),
        col_widths=(gen.page_width - inch) / 4,
        caption="Peripheral Metrics",
    )
    gen.add_table(
        make_table(central_overall),
        col_widths=(gen.page_width - inch) / 4,
        caption="Central Metrics",
    )

    gen.add_table(
        make_misc_table(misc_data),
        col_widths=(gen.page_width - inch) * 3 / 8,
        caption="Misc. Metrics",
    )

    gen.new_page()
    gen.add_table(
        make_version_table(),
        col_widths=(gen.page_width - gen.rlib.units.inch) * 3 / 8,
        caption="Version Info",
    )

    date = now.strftime("%m/%d/%y")
    gen.build(doc_title=f"BLE Connection Stability Report {date}")


def save_results(
    periph, central, sample_rate, misc_data: dict, phy: str, directory: str
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

    save_per_plot(periph, central, sample_rate=sample_rate, directory=directory)

    save_individual(
        data=periph,
        sample_rate=sample_rate,
        label=f"Peripheral_{phy}",
        directory=directory,
    )
    save_individual(
        data=central,
        sample_rate=sample_rate,
        label=f"Central_{phy}",
        directory=directory,
    )

    add_pdf(periph[-1], central[-1], directory, misc_data)


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
        description="Evaluates conne perfomrance and stability over a long period of time",
    )

    parser.add_argument("central", help="Central board")
    parser.add_argument("peripheral", help="Peripheral Board")
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


def connect(periph: BleHci, central: BleHci):
    central_addr = 0x001234887733
    periph_addr = 0x111234887733

    periph.reset()
    central.reset()
    central.set_adv_tx_power(0)
    periph.set_adv_tx_power(0)
    periph.set_address(periph_addr)
    central.set_address(central_addr)

    periph.start_advertising(connect=True)
    central.init_connection(addr=periph_addr)


def main():
    global reconnect
    # pylint: disable=too-many-locals
    """MAIN"""

    args = config_cli()

    central_board: str = args.central
    periph_board: str = args.peripheral

    if central_board == periph_board:
        raise ValueError(
            f"Central must not be the same as peripheral, {central_board} = {periph_board}"
        )

    resource_manager = ResourceManager()

    sample_rate = args.sample_rate if args.sample_rate >= 1 else 1
    iterations = int(int(args.time) / float(sample_rate))
    assert isinstance(iterations, int)

    central_hci_port = resource_manager.get_item_value(f"{central_board}.hci_port")
    periph_hci_port = resource_manager.get_item_value(f"{periph_board}.hci_port")

    central = BleHci(
        central_hci_port,
        async_callback=hci_callback,
        evt_callback=hci_callback,
        id_tag="central",
    )

    periph = BleHci(
        periph_hci_port,
        async_callback=hci_callback,
        evt_callback=hci_callback,
        id_tag="periph",
    )

    periph_cummulative = []
    central_cummulative = []

    misc = {
        "Dropped Connections": 0,
        "Timeouts": 0,
        "Central Board": central_board,
        "Peripheral Board": periph_board,
        "Central Target": resource_manager.get_item_value(f"{central_board}.target"),
        "Peripheral Target": resource_manager.get_item_value(f"{periph_board}.target"),
        "Central Package": resource_manager.get_item_value(
            f"{central_board}.package", "NULL"
        ),
        "Peripheral Package": resource_manager.get_item_value(
            f"{periph_board}.package", "NULL"
        ),
    }

    start_time = datetime.now()

    connect(periph, central)

    # Preliminary read. Seems like the first read is always empty
    try:
        periph.get_conn_stats()
        central.get_conn_stats()
    except:
        pass

    with alive_bar(iterations) as bar:
        for _ in range(iterations):
            try:
                periph_stats, _ = periph.get_conn_stats()
                periph_cummulative.append(periph_stats)
            except TimeoutError or TypeError:
                misc["Timeouts"] += 1
                periph_cummulative.append(DataPktStats())

            try:
                central_stats, _ = central.get_conn_stats()
                central_cummulative.append(central_stats)
            except TimeoutError or TypeError:
                misc["Timeouts"] += 1
                central_cummulative.append(DataPktStats())

            if reconnect:
                misc["Dropped Connections"] += 1
                try:
                    connect(periph, central)
                    reconnect = False
                except TimeoutError:
                    misc["Timeouts"] += 1

            bar()
            time.sleep(sample_rate)

    try:
        periph_stats, _ = periph.get_conn_stats()
        central_stats, _ = central.get_conn_stats()
        periph_cummulative.append(periph_stats)
        central_cummulative.append(central_stats)
        central.disconnect()
        periph.disconnect()
        central.reset()
        periph.reset()
    except TimeoutError:
        pass

    misc["Start Time"] = start_time.strftime("%H:%M:%S")
    misc["Stop Time"] = datetime.now().strftime("%H:%M:%S")

    print("[cyan]Plotting results. This may take some time[/cyan]")
    save_results(
        periph=periph_cummulative,
        central=central_cummulative,
        misc_data=misc,
        phy=args.phy,
        sample_rate=sample_rate,
        directory=args.directory,
    )


if __name__ == "__main__":
    main()
