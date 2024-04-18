#! /usr/bin/env python3
###############################################################################
#
# Copyright (C) 2022-2023 Maxim Integrated Products, Inc., All Rights Reserved.
# (now owned by Analog Devices, Inc.)
#
# This software is protected by copyright laws of the United States and
# of foreign countries. This material may also be protected by patent laws
# and technology transfer regulations of the United States and of foreign
# countries. This software is furnished under a license agreement and/or a
# nondisclosure agreement and may only be used or reproduced in accordance
# with the terms of those agreements. Dissemination of this information to
# any party or parties not specified in the license agreement and/or
# nondisclosure agreement is expressly prohibited.
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
###############################################################################
#
# Copyright (C) 2023 Analog Devices, Inc. All Rights Reserved.
#
# This software is proprietary and confidential to Analog Devices, Inc. and
# its licensors.
#
###############################################################################
"""
datsc_connected.py

Description: Data server-client connection test

"""
import sys
import serial
import os
import time
import threading
import datetime

sys.path.append("..")
from Resource_Share.resource_manager import ResourceManager


def test_secure_connection(serial_port: serial.Serial):
    start = datetime.now()

    while True:
        text = str(serial_port.readline())
        print(text)
        # wait until you see the term passkey, so we can enter the pin
        if "enter passkey" in text:
            time.sleep(1)
            serial_port.write("pin 1 1234\r\n".encode("utf-8"))
            break

        if (datetime.now() - start).total_seconds > 10:
            print("TIMEOUT!!")
            return False

    start = datetime.now()
    while True:
        text = str(serial_port.readline())
        # wait for pairing process to go through and see if it passed or failed
        if "Pairing failed" in text:
            print("Pairing failed")
            return False
        elif "Pairing completed successfully" in text:
            print("Pairing success")
            return True

        if (datetime.now() - start).total_seconds > 10:
            print("TIMEOUT!!")
            return False


def client_thread(portname: str):
    test_results_client = {}

    client_console = serial.Serial(portname, baudrate=115200)
    test_results_client["pairing"] = test_secure_connection(client_console)

    return test_results_client


def server_thread(portname: str):
    test_results_server = {}
    server_console = serial.Serial(portname, baudrate=115200)
    test_results_server["pairing"] = test_secure_connection(server_console)

    return test_results_server


def print_results(name, report):
    overall = True

    print(f"{name} RESULTS")
    print("TEST\t\tResult")
    for key, value in report.items():
        print(f"{key}\t\t{value}")

        if not value:
            overall = False

    return overall


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Not enough arguments!")
        sys.exit(-1)

    if len(sys.argv) > 3:
        custom_config = sys.argv[3]
    else:
        custom_config = None

    rm = ResourceManager()

    # Get the boards under test
    server_board = sys.argv[1]
    client_board = sys.argv[2]

    # Get console ports associated with the boards
    server_port = rm.get_item_value(f"{server_board}.console_port")
    client_port = rm.get_item_value(f"{client_board}.console_port")

    # Configure and run tests
    client_t = threading.Thread(target=client_thread, args=(client_port,))
    server_t = threading.Thread(target=server_thread, args=(server_port,))
    client_t.start()
    server_t.start()
    client_results: dict = client_t.join()
    server_results: dict = server_t.join()

    # Print Results
    overall_client = print_results("DATC", client_results)
    overall_server = print_results("DATS", server_results)

    print(f"Client {'Pass' if overall_client else 'Fail'}")
    print(f"Client {'Pass' if overall_client else 'Fail'}")
    print(f"Overall {'Pass' if overall_client and overall_server else 'Fails'}")
