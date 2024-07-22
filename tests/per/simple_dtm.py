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
import sys
from rich import print

# pylint: disable=import-error,wrong-import-position

from max_ble_hci import BleHci
from max_ble_hci.constants import PhyOption
from resource_manager import ResourceManager
from datetime import datetime

# pylint: enable=import-error,wrong-import-position


def config_cli():
    parser = argparse.ArgumentParser(
        description="Form basic DTM test to show minimum viability",
    )

    parser.add_argument("central", help="Central board")
    parser.add_argument("peripheral", help="Peripheral Board")

    parser.add_argument("-c", "--channel", default="0", help="RF Channel")
    parser.add_argument("--phy", default="1M", help="Connection PHY (1M, 2M, S2, S8)")

    parser.add_argument(
        "-pl", "--packet-length", default=0, help="Packet length 0 - 255"
    )
    parser.add_argument(
        "-t",
        "--time",
        default=0,
        help="Time to run program. If 0, until CTRL-C Entered",
    )

    return parser.parse_args()


def main():
    # pylint: disable=too-many-locals
    """MAIN"""

    args = config_cli()

    central_board = args.central
    periph_board = args.peripheral

    rmanager = ResourceManager()
    central_hci_port = rmanager.get_item_value(f"{central_board}.hci_port")
    periph_hci_port = rmanager.get_item_value(f"{periph_board}.hci_port")

    central = BleHci(
        central_hci_port,
        id_tag="central",
    )
    periph = BleHci(
        periph_hci_port,
        id_tag="periph",
    )

    channel = int(args.channel)
    phy = PhyOption.str_to_enum(args.phy)
    duration = int(args.time)

    central.reset()
    periph.reset()

    periph.rx_test(channel=channel, phy=phy)
    central.tx_test(channel=channel, phy=phy, packet_len=int(args.packet_length))

    start = datetime.now()

    while (
        duration and (datetime.now() - start).total_seconds() <= duration
    ) or not duration:
        try:
            stats_tx, _ = central.get_test_stats()
            stats_rx, _ = periph.get_test_stats()

            print(f"Received: {stats_rx.rx_data}")
            print(f"Timeouts: {stats_rx.rx_data_timeout}")
            print(f"CRC {stats_rx.rx_data_crc}")
            print(f"PER: {round(stats_rx.per(stats_tx.tx_data),2)}%")

            central.reset_test_stats()
            periph.reset_test_stats()

            time.sleep(5)
        except KeyboardInterrupt:
            try:
                central.reset()
                periph.reset()
            except:
                pass
            sys.exit(0)
        except:
            pass

        elapsed = round((datetime.now() - start).total_seconds(),2)
        print(f"Time Elapsed {elapsed}")


if __name__ == "__main__":
    main()
