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
import argparse
import sys
import time
from typing import Dict

import matplotlib.pyplot as plt
import pandas as pd
from ble_test_suite.equipment import mc_rcdat_6000, mc_rf_sw
from ble_test_suite.results import Mask, Plot
from ble_test_suite.utils.log_util import get_formatted_logger
from ble_test_suite.results.report_generator import ReportGenerator

# pylint: disable=import-error,wrong-import-position

from max_ble_hci import BleHci
from max_ble_hci.packet_codes import StatusCode
from max_ble_hci.hci_packets import EventPacket
from max_ble_hci.packet_codes import EventCode
from max_ble_hci.data_params import EstablishConnParams
from max_ble_hci.constants import PhyOption
from resource_manager import ResourceManager
from serial import Timeout
from utils import config_switches, create_directory, make_version_table
from datetime import datetime

# pylint: enable=import-error,wrong-import-position


def print_test_config(slave, master):
    print("Using:")
    print(f"\tSlave - {slave}")
    print(f"\tMaster - {master}\n")


def config_cli():
    parser = argparse.ArgumentParser(
        description="Evaluates connection sensitivity",
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
    parser.add_argument(
        "--local",
        action="store_true",
        help="Conditionally skip code only used on CI machine",
    )

    return parser.parse_args()


class SensitivityConnTest:
    def __init__(
        self,
        periph_board: str,
        central_board: str,
        phy: str,
        directory: str,
        local=True,
    ) -> None:
        self.periph_board = periph_board
        self.central_board = central_board
        self.phy = PhyOption.str_to_enum(phy)
        self.directory = directory
        self.periph: BleHci
        self.central: BleHci

        self.resource_manager = ResourceManager()

        if not local:
            config_switches(
                resource_manager=self.resource_manager,
                slave=periph_board,
                master=central_board,
            )

        central_hci_port = self.resource_manager.get_item_value(
            f"{central_board}.hci_port"
        )
        periph_hci_port = self.resource_manager.get_item_value(
            f"{periph_board}.hci_port"
        )

        try:
            self.loss = self.resource_manager.get_item_value("rf_bench.cal.losses.2440")
            self.loss = float(self.loss)
        except KeyError:
            print("Could not find cal data in config. Defaulting to 0")
            self.loss = 0.0

        self.central = BleHci(
            central_hci_port,
            async_callback=self.hci_callback,
            evt_callback=self.hci_callback,
            id_tag="central",
        )
        self.periph = BleHci(
            periph_hci_port,
            async_callback=self.hci_callback,
            evt_callback=self.hci_callback,
            id_tag="periph",
        )

        self.reconnect = False
        self.start_time = None
        self.stop_time = None

    def connect(self):
        central_addr = 0x001234887733
        periph_addr = 0x111234887733

        self.periph.reset()
        self.central.reset()
        self.central.set_adv_tx_power(0)
        self.periph.set_adv_tx_power(0)
        self.periph.set_address(periph_addr)
        self.central.set_address(central_addr)

        self.periph.start_advertising(connect=True)
        self.central.init_connection(addr=periph_addr)

        # Default is 1M
        if self.phy != PhyOption.PHY_1M:
            err = self.periph.set_phy(tx_phys=self.phy, rx_phys=self.phy)
            if err != StatusCode.SUCCESS:
                print("Error setting phy!")

    def save_results(self, results: Dict[str, list]):
        """Store PER Results

        Parameters
        ----------
        results : Dict[str,list]
            Results from per sweep
        """
        create_directory(self.directory)

        df = pd.DataFrame(results)

        df.to_csv(f"{self.directory}/per_connection.csv", index=False)

        fail_bar = [30] * len(results["attens"])

        sens_plot_path = f"{self.directory}/per_connection.png"

        plt.plot(df["attens"], df["slave"], label=f"Peripheral")
        plt.plot(df["attens"], df["master"], label=f"Central")
        plt.plot(df["attens"], fail_bar)

        plt.title("Central and Peripheral PER vs Attenuation")
        plt.xlabel(f"Received Power (dBm)")
        plt.ylabel(f"PER %")
        plt.legend()
        plt.savefig(sens_plot_path)

        now = datetime.now()
        gen = ReportGenerator(f'connection_sensitivity_{now.strftime("%m_%d_%y")}.pdf')

        gen.new_page()
        gen.add_image(sens_plot_path)

        below_spec_p = df[df["slave"] > 30.8]
        below_spec_c = df[df["master"] > 30.8]

        if len(below_spec_p) > 0:
            sens_point_periph = below_spec_p[0]
        else:
            sens_point_periph = float("-inf")

        if len(below_spec_c) > 0:
            sens_point_central = below_spec_c[0]
        else:
            sens_point_central = float("-inf")

        result_table = [
            ["Title", "Value", "Unit"],
            ["Peripheral Sensitivity", round(sens_point_periph, 2), "dBm"][
                "Central Sensitivity", round(sens_point_central, 2), "dBm"
            ],
        ]

        gen.add_table(
            result_table,
            col_widths=(gen.page_width - gen.rlib.units.inch) * 4,
            caption="Misc Info",
        )

        misc_info_table = [
            ["", ""],
            ["Central", self.central_board],
            [
                "Central Target",
                self.resource_manager.get_item_value(f"{self.central_board}.target"),
            ],
            [
                "Central Package",
                self.resource_manager.get_item_value(f"{self.central_board}.package"),
            ],
            ["Peripheral", self.periph_board],
            [
                "Peripheral Target",
                self.resource_manager.get_item_value(f"{self.periph_board}.target"),
            ],
            [
                "Peripheral Target",
                self.resource_manager.get_item_value(f"{self.periph_board}.package"),
            ],
            ["Date", now.strftime("%m/%d/%y")],
            ["Stop Time", self.start_time.strftime("%H:%M:%S")],
            ["Stop Time", self.stop_time.strftime("%H:%M:%S")],
            [
                "Total Time",
                f"{int((self.stop_time - self.start_time).total_seconds())} s",
            ],
        ]

        gen.add_table(
            misc_info_table,
            col_widths=(gen.page_width - gen.rlib.units.inch) * 3 / 8,
            caption="Misc Info",
        )

        gen.add_table(
            make_version_table(),
            col_widths=(gen.page_width - gen.rlib.units.inch) * 3 / 7,
            caption="Version Info",
        )

        gen.build(f"Connection Sensitivity {now.strftime('%m-%d-%y')}")

    def run(self):
        # could disable with local, but then you might as well use the stability test
        atten = mc_rcdat_6000.RCDAT6000()
        attens = list(range(20, 100, 2))

        results = {"attens": [], "slave": [], "master": []}
        failed_per = False
        total_dropped_connections = 0

        prev_rx = 100000
        retries = 3

        self.start_time = datetime.now()
        self.connect()

        while attens:
            i = attens[0]
            if prev_rx == i:
                retries -= 1

            print(f"RX Power {-i} dBm")
            calibrated_value = int(i + self.loss)

            atten.set_attenuation(calibrated_value)

            time.sleep(1)

            try:
                periph_stats, _ = self.periph.get_conn_stats()
                central_stats, _ = self.central.get_conn_stats()
            except TimeoutError:
                break

            if periph_stats.rx_data and central_stats.rx_data:
                retries = 3
                periph_per = periph_stats.per()
                central_per = central_stats.per()

                print("Slave - ", periph_per)
                print("Master - ", central_per)

                results["slave"].append(periph_per)
                results["master"].append(central_per)
                results["attens"].append(-i)
                attens.pop(0)

                if (periph_per >= 30 or central_per >= 30) and i < 70:
                    failed_per = True
                    print(f"Connection Failed PER TEST at {i}")
                    print(f"Master: {central_per}, Slave: {periph_per}")

            elif reconnect:
                print("Attempting reconnect!")
                try:
                    self.connect()
                    reconnect = False
                    total_dropped_connections += 1
                except:
                    pass

            prev_rx = i
            if retries == 0:
                break

            self.periph.reset_connection_stats()
            self.central.reset_connection_stats()

        try:
            self.central.disconnect()
            self.periph.disconnect()

            self.central.reset()
            self.periph.reset()
        except TimeoutError:
            pass

        self.stop_time = datetime.now()

        self.save_results(results)

        if failed_per:
            return -1

        return 0

    def hci_callback(packet):
        if not isinstance(packet, EventPacket):
            print(packet)
            return

        global reconnect

        event: EventPacket = packet
        if event.evt_code == EventCode.DICON_COMPLETE:
            reconnect = True


def main():
    # pylint: disable=too-many-locals
    """MAIN"""

    args = config_cli()

    central_board = args.central
    periph_board = args.peripheral
    results_dir = args.directory

    print_test_config(periph_board, central_board)

    assert (
        central_board != periph_board
    ), f"Master must not be the same as slave, {central_board} = {periph_board}"

    test = SensitivityConnTest(
        periph_board=periph_board,
        central_board=central_board,
        phy=args.phy,
        directory=results_dir,
        local=args.local,
    )

    err = test.run()

    sys.exit(err)


if __name__ == "__main__":
    main()
