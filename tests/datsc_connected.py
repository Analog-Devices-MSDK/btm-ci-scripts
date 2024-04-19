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
from datetime import datetime

sys.path.append("..")
from Resource_Share.resource_manager import ResourceManager


def advertising_test(serial_port: serial.Serial):
    print("Advertising test")
    start = datetime.now()

    while True:
        text = str(serial_port.readline())

        if "Advertising started" in text:
            return True
        elif (datetime.now() - start).total_seconds() > 10:
            print("TIMEOUT!!")
            return False


def test_secure_connection(serial_port: serial.Serial):
    print("STARTING CONNECTION TEST")

    start = datetime.now()

    while True:
        text = str(serial_port.readline())
        print(text)
        # wait until you see the term passkey, so we can enter the pin
        if "enter passkey" in text:
            time.sleep(1)
            serial_port.write("pin 1 1234\r\n".encode("utf-8"))
            break

        if (datetime.now() - start).total_seconds() > 10:
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

        if (datetime.now() - start).total_seconds() > 10:
            print("TIMEOUT!!")
            return False


def write_char_test(serial_port: serial.Serial):
    print("WRITE CHARACTERISTIC TEST")
    serial_port.write("btn 2 l\r\n".encode("utf-8"))
    start = datetime.now()

    while True:
        text = str(serial_port.readline())
        if "No action assigned" in text:
            return False
        elif "hello" in text:
            return True
        elif (datetime.now() - start).total_seconds() > 10:
            print("TIMEOUT!!")
            return False


def write_secure_test(serial_port: serial.Serial):
    print("WRITE SECURE TEST")
    serial_port.write("btn 2 m\r\n".encode("utf-8"))
    start = datetime.now()

    while True:
        text = str(serial_port.readline())
        if "No action assigned" in text:
            print(text)
            return False
        elif "hello" in text:
            return True
        elif (datetime.now() - start).total_seconds() > 10:
            print("TIMEOUT!!")
            return False


def phy_switch_test(serial_port: serial.Serial):
    print("PHY CHANGE TEST")
    serial_port.write("btn 2 s\r\n".encode("utf-8"))
    start = datetime.now()

    while True:
        text = str(serial_port.readline())
        if "No action assigned" in text:
            return False
        elif "2 MBit TX and RX PHY Requested" in text:
            return True
        elif (datetime.now() - start).total_seconds() > 10:
            print("TIMEOUT!!")
            return False


def speed_test(serial_port: serial.Serial):
    print("SPEED TEST")
    serial_port.write("btn 2 x\r\n".encode("utf-8"))
    start = datetime.now()

    try:
        serial_port.readline()
    except TimeoutError:
        return False

    time.sleep(2)
    serial_port.write("btn 2 m\r\n".encode("utf-8"))

    while True:
        text = str(serial_port.readline())
        if "bps" in text:
            print(text)
            return True
        elif (datetime.now() - start).total_seconds() > 10:
            print("TIMEOUT!!")
            return False


test_results_client = {}


def client_thread(portname: str):
    client_console = serial.Serial(portname, baudrate=115200, timeout=2)
    test_results_client["pairing"] = test_secure_connection(client_console)
    test_results_client["write characteristic"] = write_char_test(client_console)
    test_results_client["write secure"] = write_secure_test(client_console)
    test_results_client['phy switch'] = phy_switch_test(client_console)
    test_results_client["speed"] = speed_test(client_console)

    return test_results_client


test_results_server = {}


def server_thread(portname: str):
    server_console = serial.Serial(portname, baudrate=115200, timeout=2)
    test_results_server["advertising"] = advertising_test(server_console)
    test_results_server["pairing"] = test_secure_connection(server_console)

    return test_results_server


def print_results(name, report):
    overall = True

    print(f"{name} RESULTS")
    print(f"{'TEST':<25} Result")
    for key, value in report.items():
        print('-'*30)
        print(f"{key:<25}{'Fail' if not value else 'Pass'}")

        if not value:
            overall = False

    print('-'*30, '\n')
    

    return overall


if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Not enough arguments!")
        sys.exit(-1)


    rm = ResourceManager()

    # Get the boards under test and the file paths
    server_board = sys.argv[1]
    client_board = sys.argv[2]
    dats_file = sys.argv[3]
    datc_file = sys.argv[4]

    # Make sure all bonding information is wiped
    rm.resource_erase(server_board)
    rm.resource_erase(client_board)

    
    rm.resource_flash(server_board, dats_file)
    rm.resource_flash(client_board, datc_file)

    # Get console ports associated with the boards
    server_port = rm.get_item_value(f"{server_board}.console_port")
    client_port = rm.get_item_value(f"{client_board}.console_port")

    # Configure and run tests
    client_t = threading.Thread(target=client_thread, args=(client_port,))
    server_t = threading.Thread(target=server_thread, args=(server_port,))
    client_t.start()
    server_t.start()

    # Reset to start from scratch
    rm.resource_reset(server_board)
    rm.resource_reset(client_board)

    client_t.join()
    server_t.join()

    # Print Results
    print('\n\n')
    overall_client = print_results("DATC", test_results_client)
    overall_server = print_results("DATS", test_results_server)

    print(f"{'Client':<10} {'Pass' if overall_client else 'Fail'}")
    print(f"{'Server':<10} {'Pass' if overall_server else 'Fail'}")
    print(f"{'Overall':<10} {'Pass' if overall_client and overall_server else 'Fail'}")
