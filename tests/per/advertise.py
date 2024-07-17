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
advertise.py

Description: Basic test collecting advertising statistics

"""


import argparse
import time
from datetime import datetime
from glob import glob
from typing import List

import matplotlib.pyplot as plt
import resource_manager

# pylint: disable=import-error,wrong-import-position
from alive_progress import alive_bar
from ble_test_suite.results.report_generator import ReportGenerator

# pylint: disable=import-error,wrong-import-position
from max_ble_hci import BleHci
from max_ble_hci.data_params import AdvPktStats
from packaging import version
from resource_manager import ResourceManager
from rich import print

from utils import create_directory, make_version_table

# pylint: enable=import-error,wrong-import-position

if version.parse(resource_manager.__version__) < version.parse("1.1.1"):
    raise RuntimeError("Resource manager of 1.1.1 or greater is required")


def config_cli():
    parser = argparse.ArgumentParser(
        description="Evaluates advertising perfomrance and stability over a long period of time",
    )

    parser.add_argument("dut", help="Central board")

    parser.add_argument("-t", "--time", default=1800, help="Test time")
    parser.add_argument(
        "-d", "--directory", default="advertisement_results", help="Result Directory"
    )

    parser.add_argument(
        "-s",
        "--sample-rate",
        default=1,
        help="Sample rate in seconds. Minimum of 1 second",
    )

    return parser.parse_args()


class AdvTest:
    def __init__(
        self, dut_board: str, sample_rate: int, duration: int, directory: str
    ) -> None:
        self.dut_board = dut_board

        self.directory = directory
        self.duration = duration
        self.sample_rate = (
            sample_rate if sample_rate >= 1 and sample_rate <= duration else 1
        )
        self.iterations = int(int(self.duration) / float(self.sample_rate))

        rmanager = ResourceManager()
        self.target = rmanager.get_item_value(f"{self.dut_board}.target")
        self.package = rmanager.get_item_value(f"{self.dut_board}.package")
        self.dut_hci_port = rmanager.get_item_value(f"{dut_board}.hci_port")
        self.dut = BleHci(self.dut_hci_port)

        self.results: List[AdvPktStats] = []

        self.start_time = datetime.now()
        self.stop_time = None

    def run(self):
        self.dut.reset()
        self.dut.start_advertising(connect=True, adv_name="adv-test")

        with alive_bar(self.iterations) as bar:
            for _ in range(self.iterations):
                try:
                    stats, _ = self.dut.get_adv_stats()
                    self.results.append(stats)
                except:
                    self.results.append(AdvPktStats())

                bar()

                time.sleep(self.sample_rate)

        try:
            stats, _ = self.dut.get_adv_stats()
            self.results.append(stats)
            self.dut.reset()
        except:
            pass

        self.stop_time = datetime.now()
        self._compile_results()

    def _add_pdf(self):
        now = datetime.now()
        filepath_date = now.strftime("%m_%d_%y")
        gen = ReportGenerator(
            f"{self.directory}/advertising_stability_report_{filepath_date}.pdf"
        )
        charts = glob(f"{self.directory}/*.png")

        inch = gen.rlib.units.inch
        for chart in charts:
            gen.add_image(chart, img_dims=(8 * inch, 6 * inch))

        gen.new_page()

        last_data = self.results[-1]
        cummulative_table = [
            ["Metric", "Value", "Unit"],
            ["TX Advertisments", last_data.tx_adv, "Count"],
            ["Scan Requests", last_data.rx_req, "Count"],
            ["Scan Request CRCs", last_data.rx_req_crc, "Count"],
            ["Scan Request Timeouts", last_data.rx_req_timeout, "Count"],
            ["Scan Responses", last_data.tx_resp, "Count"],
            ["Adv Errors", last_data.err_adv, "Count"],
            ["RX Setup", last_data.rx_setup, "usec"],
            ["TX Setup", last_data.tx_setup, "usec"],
            ["RX ISR", last_data.rx_isr, "usec"],
            ["TX ISR", last_data.tx_isr, "usec"],
            ["TX Chain", last_data.tx_chain if last_data.tx_chain else 0, "Count"],
            ["Scan Request Rate", round(last_data.scan_request_rate(), 2), "%"],
            ["Scan Request CRC Rate", round(last_data.scan_request_crc_rate(), 2), "%"],
            [
                "Scan Request Timeout Rate",
                round(last_data.scan_request_timeout_rate(), 2),
                "%",
            ],
            [
                "Scan Request Fulfillment",
                round(last_data.scan_req_fulfillment(), 2),
                "%",
            ],
        ]

        gen.add_table(
            cummulative_table,
            col_widths=(gen.page_width - inch) / 4,
            caption="Cummulative Advertising Metrics",
        )

        misc_info_table = [
            ["Title", "Value"],
            ["DUT", self.dut_board],
            ["Target", self.target],
            ["Package", self.package],
            ["Date", now.strftime("%m/%d/%y")],
            ["Stop Time", self.start_time.strftime("%H:%M:%S")],
            ["Stop Time", self.stop_time.strftime("%H:%M:%S")],
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

        date = now.strftime("%m/%d/%y")
        gen.build(doc_title=f"BLE Advertising Stability Report {date}")

    def _add_plots(self):
        tx_data = []

        scan_responses = []
        scan_requests = []

        rx_isr = []
        tx_isr = []

        rx_setup = []
        tx_setup = []

        req_rate = []
        crc_rate = []
        timeout_rate = []
        fulfillment_rate = []

        stat: scan_requests
        for stat in self.results:
            tx_data.append(stat.tx_adv)

            scan_requests.append(stat.rx_req)
            scan_responses.append(stat.tx_resp)
            rx_isr.append(stat.rx_isr)
            tx_isr.append(stat.tx_isr)
            tx_setup.append(stat.tx_setup)
            rx_setup.append(stat.rx_setup)

            req_rate.append(stat.scan_request_rate())
            crc_rate.append(stat.scan_request_crc_rate())
            timeout_rate.append(stat.scan_request_timeout_rate())
            fulfillment_rate.append(stat.scan_req_fulfillment())

        time_data = [x * self.sample_rate for x in range(len(self.results))]

        plt.plot(time_data, tx_data)
        plt.xlabel("Time (sec)")
        plt.ylabel("Advertisments")
        plt.title("Advertismenets Vs. Time")
        plt.savefig(f"{self.directory}/advertisiments.png")
        plt.close()

        plt.plot(time_data, scan_responses, label="Scan Response")
        plt.plot(time_data, scan_requests, label="Scan Request")
        plt.xlabel("Time (sec)")
        plt.ylabel("Packet Count")
        plt.title("Scan Requests and Responses")
        plt.legend()
        plt.savefig(f"{self.directory}/scan_req_resp.png")

        plt.close()

        plt.plot(time_data, req_rate, label="Scan Request Rate")
        plt.plot(time_data, crc_rate, label="Scan Request CRC Rate")
        plt.plot(time_data, timeout_rate, label="Scan Request Timeout Rate")
        plt.ylim([0, 100])
        plt.xlabel("time (sec)")
        plt.ylabel("Rate (%)")
        plt.title("Scan Request Metrics Vs. Time")
        plt.legend()
        plt.savefig(f"{self.directory}/requets_metrics.png")
        plt.close()

        # ISR Timing
        plt.plot(time_data, rx_isr, label="RX ISR")
        plt.plot(time_data, tx_isr, label="TX ISR")
        plt.xlabel("Time (sec)")
        plt.ylabel("ISR Time (usec)")
        plt.title("ISR Timing")
        plt.legend()
        plt.savefig(f"{self.directory}/isr_timing.png")
        plt.close()

        # Setup Timing
        plt.plot(time_data, rx_setup, label="RX SETUP")
        plt.plot(time_data, tx_setup, label="TX SETUP")
        plt.xlabel("Time (sec)")
        plt.ylabel("Setup Time (usec)")
        plt.title("Setup Timing")
        plt.legend()
        plt.savefig(f"{self.directory}/setup_timing.png")
        plt.close()

    def _compile_results(self):
        create_directory(self.directory)

        self._add_plots()
        self._add_pdf()


def main():
    # pylint: disable=too-many-locals
    """MAIN"""

    args = config_cli()

    dut_board = args.dut

    adv_test = AdvTest(
        dut_board=dut_board,
        sample_rate=int(args.sample_rate),
        duration=int(args.time),
        directory=args.directory,
    )

    adv_test.run()


if __name__ == "__main__":
    main()
