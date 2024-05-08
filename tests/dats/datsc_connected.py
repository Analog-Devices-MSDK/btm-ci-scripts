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
import os
import sys
import threading
import time
from datetime import datetime

import serial

# RESOURCE_SHARE_DIR = os.environ.get("RESOURCE_SHARE_DIR")

# if RESOURCE_SHARE_DIR is None:
#     print("Cannot find resource share directory in environment!")
#     sys.exit(-1)


# sys.path.append(RESOURCE_SHARE_DIR)
sys.path.append('../..')

# pylint: disable=import-error,wrong-import-position
from Resource_Share.resource_manager import ResourceManager

# pylint: enable=import-error,wrong-import-position


def slow_write(serial_port: serial.Serial, data: bytes):
    """Write UART data at human typing speeds

    Parameters
    ----------
    serial_port : serial.Serial
        Port to write data to
    data : bytes
        Data to write out
    """
    for byte in data:
        serial_port.write(byte)
        time.sleep(0.1)


def test_secure_connection(serial_port: serial.Serial) -> bool:
    """Generic secure connection test for pairing

    Parameters
    ----------
    serial_port : serial.Serial
        serial port to write and read from

    Returns
    -------
    bool
        True if test success. False otherwise
    """

    print("STARTING CONNECTION TEST")
    start = datetime.now()
    text = ""
    while True:
        new_text = serial_port.read(serial_port.in_waiting).decode("utf-8")
        text += new_text

        print(new_text, end='')

        # wait until you see the term passkey, so we can enter the pin
        if "passkey" in text:
            time.sleep(1)
            serial_port.write("pin 1 1234\n".encode("utf-8"))
            break

        if "Connection encrypted" in text:
            return True

        if (datetime.now() - start).total_seconds() > 20:
            print("TIMEOUT!!")
            return False

    print("Passkey entered")
    start = datetime.now()
    while True:
        new_text = serial_port.read(serial_port.in_waiting).decode("utf-8")
        text += new_text
        print(new_text, end='')


        # wait for pairing process to go through and see if it passed or failed
        if "Pairing failed" in text:
            print("Pairing failed")
            return False

        if "Pairing completed successfully" in text or "Connection encrypted" in text:
            print("Pairing success")
            return True

        if (datetime.now() - start).total_seconds() > 10:
            print("TIMEOUT!!")
            return False


def write_char_test(serial_port: serial.Serial) -> bool:
    """Test for unsecure write characteristic

    Parameters
    ----------
    serial_port : serial.Serial
        serial port to write to

    Returns
    -------
    bool
        True if test passed. False otherwise.
    """
    time.sleep(2)
    print("WRITE CHARACTERISTIC TEST")

    serial_port.write("btn 2 l\n".encode("utf-8"))
    time.sleep(1)
    serial_port.write("btn 2 l\n".encode("utf-8"))

    start = datetime.now()

    text = ""

    while True:
        new_text = serial_port.read(serial_port.in_waiting).decode("utf-8")
        text += new_text
        print(new_text, end='')

        if "No action assigned" in text:
            return False

        if "hello" in text:
            return True

        if (datetime.now() - start).total_seconds() > 10:
            print("TIMEOUT!!")
            return False

        time.sleep(0.5)
        serial_port.write("btn 2 l\n".encode("utf-8"))


def write_secure_test(serial_port: serial.Serial) -> bool:
    """Test for secure write

    Parameters
    ----------
    serial_port : serial.Serial
        Serial port to write to

    Returns
    -------
    bool
        True if test passed. False otherwise.
    """
    print("WRITE SECURE TEST")
    time.sleep(3)
    serial_port.write("btn 2 m\n".encode("utf-8"))

    start = datetime.now()
    text = ""
    while True:
        new_text = serial_port.read(serial_port.in_waiting).decode("utf-8")
        text += new_text
        print(new_text, end='')

        if "No action assigned" in text:
            return False

        if "hello" in text or "Secure data received!" in text:
            return True
        if (datetime.now() - start).total_seconds() > 10:
            print("TIMEOUT!!")
            return False

        time.sleep(1)
        serial_port.write("btn 2 m\r\n".encode("utf-8"))


def phy_switch_test(serial_port: serial.Serial) -> bool:
    """Test to update PHY from 1M to 2M

    Parameters
    ----------
    serial_port : serial.Serial
        Serial port to write to

    Returns
    -------
    bool
        True if test passed. False otherwise.
    """
    time.sleep(4)
    print("PHY CHANGE TEST")

    serial_port.write("btn 2 s\n".encode("utf-8"))
    start = datetime.now()
    text = ""

    while True:
        new_text = serial_port.read(serial_port.in_waiting).decode("utf-8")
        text += new_text
        print(new_text, end='')


        if "No action assigned" in text:
            return False

        if "2 MBit TX and RX PHY Requested" in text:
            return True

        if (datetime.now() - start).total_seconds() > 10:
            print("TIMEOUT!!")
            return False

        time.sleep(1)
        serial_port.write("btn 2 s\n".encode("utf-8"))


def _run_speed_test(serial_port: serial.Serial):
    serial_port.write("btn 2 x\n".encode("utf-8"))
    time.sleep(1)
    serial_port.write("btn 2 m\n".encode("utf-8"))


def speed_test(serial_port: serial.Serial) -> bool:
    """Test throughput example

    Parameters
    ----------
    serial_port : serial.Serial
        Serial port to write to

    Returns
    -------
    bool
        True if test passed. False otherwise.
    """
    print("SPEED TEST")

    text = ""

    _run_speed_test(serial_port)
    time.sleep(1)
    start = datetime.now()

    while True:
        new_text = serial_port.read(serial_port.in_waiting).decode("utf-8")
        text += new_text
        print(new_text, end='')

        if "bps" in text:
            print(text)
            return True

        if (datetime.now() - start).total_seconds() > 20:
            print("TIMEOUT!!")
            return False

        _run_speed_test(serial_port)
        time.sleep(2)


test_results_client = {}


def _client_thread(portname: str):
    
    client_console = serial.Serial(portname, baudrate=115200, timeout=2)
    client_console.flush()
    test_results_client["pairing"] = test_secure_connection(client_console)
    if not test_results_client["pairing"]:
        return test_results_client
    test_results_client["write characteristic"] = write_char_test(client_console)
    test_results_client["write secure"] = write_secure_test(client_console)

    test_results_client["phy switch"] = phy_switch_test(client_console)
    test_results_client["speed"] = speed_test(client_console)

    client_console.flush()

    return test_results_client


test_results_server = {}


def _server_thread(portname: str):
    server_console = serial.Serial(portname, baudrate=115200, timeout=2)
    server_console.flush()
    test_results_server["pairing"] = test_secure_connection(server_console)

    return test_results_server


def _print_results(name, report):
    overall = True

    print(f"{name} RESULTS")
    print(f"{'TEST':<23} Result")
    for key, value in report.items():
        print("-" * 30)
        print(f"{key:<25}{'Fail' if not value else 'Pass'}")

        if not value:
            overall = False

    print("-" * 30, "\n")

    return overall


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Not enough arguments!")
        sys.exit(-1)

    rm = ResourceManager()

    # Get the boards under test and the file paths
    SERVER_BOARD = sys.argv[1]
    CLIENT_BOARD = sys.argv[2]
    

    # sanity check
    assert (
        SERVER_BOARD != CLIENT_BOARD
    ), f"Client Board ({CLIENT_BOARD}) must not  be the same as Server ({SERVER_BOARD})"

    # Get console ports associated with the boards
    server_port = rm.get_item_value(f"{SERVER_BOARD}.console_port")
    client_port = rm.get_item_value(f"{CLIENT_BOARD}.console_port")

    # Configure and run tests
    client_t = threading.Thread(target=_client_thread, args=(client_port,))
    server_t = threading.Thread(target=_server_thread, args=(server_port,))

    # Reset to start from scratch
    owner = rm.get_owner(SERVER_BOARD)
    rm.resource_reset(SERVER_BOARD,owner)
    rm.resource_reset(CLIENT_BOARD,owner)

    client_t.start()
    server_t.start()

    client_t.join()
    server_t.join()

    # Print Results
    print("\n\n")
    OVERALL_CLIENT = _print_results("DATC", test_results_client)
    OVERALL_SERVER = _print_results("DATS", test_results_server)

    print(f"{'Client':<10} {'Pass' if OVERALL_CLIENT else 'Fail'}")
    print(f"{'Server':<10} {'Pass' if OVERALL_SERVER else 'Fail'}")
    print(f"{'Overall':<10} {'Pass' if OVERALL_CLIENT and OVERALL_SERVER else 'Fail'}")

    if not OVERALL_CLIENT or not OVERALL_SERVER:
        sys.exit(-1)
