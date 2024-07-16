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
from max_ble_hci.data_params import ScanPktStats, ScanParams
from max_ble_hci.packet_codes import StatusCode
from packaging import version
from resource_manager import ResourceManager
from rich import print

from utils import create_directory, make_version_table

# pylint: enable=import-error,wrong-import-position

if version.parse(resource_manager.__version__) < version.parse("1.1.1"):
    raise RuntimeError("Resource manager of 1.1.1 or greater is required")


class ScanTest:
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
        dut_hci_port = rmanager.get_item_value(f"{dut_board}.hci_port")
        self.dut = BleHci(dut_hci_port)

        self.results: List[ScanPktStats] = []
        self.start_time = datetime.now()
        self.stop_time = None

    def run(self):
        self.dut.reset()
        self.dut.set_scan_params(scan_params=ScanParams(scan_interval=0x10))
        self.dut.enable_scanning(True)

        with alive_bar(self.iterations) as bar:
            for _ in range(self.iterations):
                try:
                    stats, err = self.dut.get_scan_stats()
                    if err == StatusCode.SUCCESS:
                        self.results.append(stats)
                except:
                    self.results.append(ScanPktStats())

                bar()

                time.sleep(self.sample_rate)

        try:
            stats, err = self.dut.get_scan_stats()
            self.dut.reset()
            if err == StatusCode.SUCCESS:
                self.results.append(stats)
        except:
            pass

        self.stop_time = datetime.now()
        self._compile_results()

    def _compile_results(self):
        create_directory(self.directory)
        self._add_plots()
        self._add_pdf()

    def _add_pdf(self):
        now = datetime.now()
        filepath_date = now.strftime("%m_%d_%y")
        gen = ReportGenerator(
            f"{self.directory}/scanning_stability_report_{filepath_date}.pdf"
        )
        charts = glob(f"{self.directory}/*.png")

        inch = gen.rlib.units.inch
        for chart in charts:
            gen.add_image(chart, img_dims=(8 * inch, 6 * inch))

        gen.new_page()

        last_data = self.results[-1]
        cummulative_table = [
            ["Metric", "Value", "Unit"],
            ["RX Advertisments", last_data.rx_adv, "Count"],
            ["Scan Requests", last_data.tx_req, "Count"],
            ["Scan Responses", last_data.rx_rsp, "Count"],
            ["Scan Response CRCs", last_data.rx_rsp_crc, "Count"],
            ["Scan Response Timeouts", last_data.rx_rsp_timeout, "Count"],
            ["Scanning Errors", last_data.err_scan, "Count"],
            ["RX Setup", last_data.rx_setup, "usec"],
            ["TX Setup", last_data.tx_setup, "usec"],
            ["RX ISR", last_data.rx_isr, "usec"],
            ["TX ISR", last_data.tx_isr, "usec"],
            ["Scan Response Rate", round(last_data.scan_response_rate(), 2), "%"],
            [
                "Scan Response CRC Rate",
                round(last_data.scan_response_crc_rate(), 2),
                "%",
            ],
            [
                "Scan Response Timeout Rate",
                round(last_data.scan_response_timeout_rate(), 2),
                "%",
            ],
            [
                "PER",
                round(last_data.per(), 2),
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

        date = now.strftime("%m/%d/%y")
        gen.build(doc_title=f"BLE Scannning Stability Report {date}")

    def _add_plots(self):
        rx_adv = []
        rx_adv_crc = []
        rx_adv_timeout = []

        scan_responses = []
        scan_response_crc = []
        scan_response_timeout = []

        scan_requests = []

        rx_isr = []
        tx_isr = []

        rx_setup = []
        tx_setup = []

        resp_rate = []
        crc_rate = []
        timeout_rate = []
        per = []

        stat: ScanPktStats
        for stat in self.results:
            rx_adv.append(stat.rx_adv)
            rx_adv_crc.append(stat.rx_adv_crc)
            rx_adv_timeout.append(stat.rx_adv_timeout)

            scan_requests.append(stat.tx_req)
            scan_responses.append(stat.rx_rsp)
            scan_response_crc.append(stat.rx_rsp_crc)
            scan_response_timeout.append(stat.rx_rsp_timeout)

            rx_isr.append(stat.rx_isr)
            tx_isr.append(stat.tx_isr)
            tx_setup.append(stat.tx_setup)
            rx_setup.append(stat.rx_setup)

            crc_rate.append(stat.scan_response_crc_rate())
            resp_rate.append(stat.scan_response_rate())
            timeout_rate.append(stat.scan_response_timeout_rate())

            per.append(stat.per())

        time_data = [x * self.sample_rate for x in range(len(self.results))]

        plt.plot(time_data, rx_adv, label="RX Adv")
        plt.plot(time_data, rx_adv_crc, label="RX ADV CRC")
        plt.plot(time_data, rx_adv_timeout, label="RX ADV TIMEOUT")

        plt.xlabel("Time (sec)")
        plt.ylabel("Advertisments")
        plt.title("Advertisements Vs. Time")
        plt.legend()
        plt.savefig(f"{self.directory}/rx_advertisiments.png")
        plt.close()

        plt.plot(time_data, per)
        plt.ylim([0, 100])
        plt.xlabel("Time (sec)")
        plt.ylabel("PER (%)")
        plt.title("PER Vs. Time")
        plt.savefig(f"{self.directory}/per.png")
        plt.close()

        plt.plot(time_data, scan_requests, label="Scan Request")
        plt.plot(time_data, scan_responses, label="Scan Response")
        plt.plot(time_data, scan_response_crc, label="Scan Response CRC")
        plt.plot(time_data, scan_response_timeout, label="Scan Response Timeout")

        plt.xlabel("Time (sec)")
        plt.ylabel("Packet Count")
        plt.title("Scan Requests and Responses")
        plt.legend()
        plt.savefig(f"{self.directory}/scan_req_resp.png")
        plt.close()

        plt.plot(time_data, resp_rate, label="Scan Response Rate")
        plt.plot(time_data, crc_rate, label="Scan Response CRC Rate")
        plt.plot(time_data, timeout_rate, label="Scan Response Timeout Rate")
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


def config_cli():
    parser = argparse.ArgumentParser(
        description="Evaluates scanning perfomrance and stability over a long period of time",
    )

    parser.add_argument("dut", help="Central board")
    parser.add_argument("-r", "--results", help="Results directory")
    parser.add_argument("-t", "--time", default=1800, help="Test time")
    parser.add_argument(
        "-d", "--directory", default="scanning_results", help="Result Directory"
    )

    parser.add_argument(
        "-s",
        "--sample-rate",
        default=1,
        help="Sample rate in seconds. Minimum of 1 second",
    )

    return parser.parse_args()


def main():
    """MAIN"""

    args = config_cli()

    test = ScanTest(
        dut_board=args.dut,
        sample_rate=int(args.sample_rate),
        duration=int(args.time),
        directory=args.directory,
    )
    test.run()


if __name__ == "__main__":
    main()
