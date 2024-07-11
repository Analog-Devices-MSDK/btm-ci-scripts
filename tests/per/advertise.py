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


import sys
import time


# pylint: disable=import-error,wrong-import-position
from max_ble_hci import BleHci
from resource_manager import ResourceManager


def main():
    # pylint: disable=too-many-locals
    """MAIN"""

    if len(sys.argv) < 1:
        print(f"Expected 2 inputs. Got {len(sys.argv)}")
        print("usage: <MASTER_BAORD> <SLAVE_BOARD> <RESULTS DIRECTORY")
        sys.exit(-1)

    dut_board = sys.argv[1]
    print(f"DUT: {dut_board}")

    resource_manager = ResourceManager()

    try:
        loss = resource_manager.get_item_value("rf_bench.cal.losses.2440")
        loss = float(loss)
    except KeyError:
        print("Could not find cal data in config. Defaulting to 0")
        loss = 0.0

    # config_switches(resource_manager, slave_board, master_board)

    dut_hci_port = resource_manager.get_item_value(f"{dut_board}.hci_port")

    time.sleep(1)

    dut = BleHci(dut_hci_port)

    dut.reset()

    dut.start_advertising(connect=False, adv_name="adv-test")

    adv_time = 10
    print(f"Advertising for {adv_time} seconds")
    time.sleep(adv_time)

    stats = dut.get_adv_stats()

    print(stats)

    req_rate = stats.scan_request_rate()
    crc_rate = stats.scan_request_crc_rate()
    fulfillment_rate = stats.scan_req_fulfillment()

    req_rate_min = 30
    crc_rate_max = 10
    fulfillment_rate_min = 95

    error_code = 0

    if req_rate < req_rate_min:
        print("Scam request rate too low")
        error_code += 1

    if crc_rate > crc_rate_max:
        print("CRC rate too high!")
        error_code += 1

    if fulfillment_rate < fulfillment_rate_min:
        print("Scan request fulfillment too low!")
        error_code += 1

    sys.exit(error_code)


if __name__ == "__main__":
    main()
