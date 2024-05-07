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
import re
import time
from datetime import datetime
from typing import Dict
import serial



sys.path.append("../..")

# pylint: disable=import-error,wrong-import-position
from Resource_Share.resource_manager import ResourceManager

# pylint: enable=import-error,wrong-import-position

BTN1 = 1
BTN2 = 2


def press_btn(serial_port: serial.Serial, btn_num: int, method: str):
    """Press button via console

    Parameters
    ----------
    serial_port : serial.Serial
        Serial port to write to
    btn_num : int
        Button number (1/2)
    method : str
        Button method (s/m/l/x)
    """
    command = f"btn {btn_num} {method}\r\n".encode("utf-8")
    serial_port.write(command)


def _slow_write(serial_port: serial.Serial, data: bytes):
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


def client_test_discover_filespace(serial_port: serial.Serial) -> bool:
    """Test discovery filespace

    Parameters
    ----------
    serial_port : serial.Serial
        Seiral port to write to

    Returns
    -------
    bool
        True if test passed. False otherwise
    """
    print("DISCOVER FILESPACE TEST")
    press_btn(serial_port, BTN2, "s")

    text = ""
    start = datetime.now()

    while True:
        new_text = serial_port.read(serial_port.in_waiting).decode("utf-8")
        text += new_text
        if new_text:
            print(new_text)

        if "File discovery complete" in text:
            return True

        if (datetime.now() - start).total_seconds() > 10:
            print("TIMEOUT!!")
            return False
        
        time.sleep(1)
        press_btn(serial_port, BTN2, "s")



def client_test_start_update_xfer(serial_port: serial.Serial) -> bool:
    """Test firmware update

    Parameters
    ----------
    serial_port : serial.Serial
        Serial port to write to

    Returns
    -------
    bool
        True if test passed. False otherwise
    """
    print("UPDATE XFER TEST")
    press_btn(serial_port, BTN2, "m")

    text = ""
    start = datetime.now()

    while True:
        new_text = serial_port.read(serial_port.in_waiting).decode("utf-8")
        text += new_text

        print(new_text)

        if "Starting file transfer" in text:
            break

        if (datetime.now() - start).total_seconds() > 10:
            print("TIMEOUT!!")
            return False

    # wait for complete
    while True:
        new_text = serial_port.read(serial_port.in_waiting).decode("utf-8")
        text += new_text

        if "transfer complete" in text:
            return True

        if (datetime.now() - start).total_seconds() > 30:
            print("TIMEOUT!!")
            return False


def client_verify_xfer(serial_port: serial.Serial) -> bool:
    """Test transfer verification

    Parameters
    ----------
    serial_port : serial.Serial
        Serial port to write to

    Returns
    -------
    bool
        True if test passed. False otherwise
    """
    print("VERIFY XFER TEST")

    press_btn(serial_port, BTN2, "l")

    text = ""
    start = datetime.now()

    pattern = r"Verify complete status:\s*(.+)"

    while True:
        new_text = serial_port.read(serial_port.in_waiting).decode("utf-8")
        text += new_text
        if new_text:
            print(new_text)
        status_match = re.search(pattern, text)

        # Check for successful completion
        if status_match:
            status = status_match.group(1) == 0
            if status == 0:
                return True
            print(f"status mismatch {status}")
            print(status)
            return False

        if (datetime.now() - start).total_seconds() > 10:
            print("TIMEOUT!!")
            return False


def client_tests(portname: str) -> Dict[str, bool]:
    """All client tests

    Parameters
    ----------
    portname : str
        Portname for console

    Returns
    -------
    Dict[str, bool]
        Test report
    """
    client_console = serial.Serial(portname, baudrate=115200, timeout=2)

    client_results = {}
    client_results["filespace"] = client_test_discover_filespace(client_console)
    client_results["update"] = client_test_start_update_xfer(client_console)
    client_results["verify"] = client_verify_xfer(client_console)

    client_console.flush()

    return client_results


def server_test_version(serial_port: serial.Serial) -> bool:
    """Test the version of firmware

    Parameters
    ----------
    serial_port : serial.Serial
        Serial port to write to

    Returns
    -------
    bool
        True if test passed. False otherwise
    """
    print("SERVER TEST VERSION")
    text = ""
    press_btn(serial_port, BTN2, "m")
    start = datetime.now()

    pattern = r"FW_VERSION:\s*(.+)"

    while True:
        new_text = serial_port.read(serial_port.in_waiting).decode("utf-8")
        text += new_text

        version_match = re.search(pattern, text)

        if version_match:
            version = version_match.group(1)
            print(f"GOT VERSION {version}")
            return True

        if (datetime.now() - start).total_seconds() > 10:
            print("TIMEOUT!!")
            return False

        time.sleep(1)
        press_btn(serial_port, BTN2, "m")


def server_tests(portname: str):
    """All server tests

    Parameters
    ----------
    portname : str
        Portname for console

    Returns
    -------
    Dict[str, bool]
        Test report
    """
    server_console = serial.Serial(portname, baudrate=115200, timeout=2)
    test_results_server = {}
    test_results_server["versioning"] = server_test_version(server_console)

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
    assert (
        SERVER_BOARD != CLIENT_BOARD
    ), f"Client Board ({CLIENT_BOARD}) must not  be the same as Server ({SERVER_BOARD})"

    OWNER = rm.get_owner(SERVER_BOARD)


    # Get console ports associated with the boards
    server_port = rm.get_item_value(f"{SERVER_BOARD}.console_port")
    client_port = rm.get_item_value(f"{CLIENT_BOARD}.console_port")

    rm.resource_reset(SERVER_BOARD, OWNER)
    time.sleep(1)
    rm.resource_reset(CLIENT_BOARD, OWNER)
    # give time for connection
    time.sleep(5)

    # Run the tests
    test_server_results = server_tests(server_port)
    test_client_results = client_tests(client_port)

    # Print Results
    print("\n\n")
    OVERALL_CLIENT = _print_results("OTAC", test_client_results)
    OVERALL_SERVER = _print_results("OTAS", test_server_results)

    print(f"{'Client':<10} {'Pass' if OVERALL_CLIENT else 'Fail'}")
    print(f"{'Server':<10} {'Pass' if OVERALL_SERVER else 'Fail'}")
    print(f"{'Overall':<10} {'Pass' if OVERALL_CLIENT and OVERALL_SERVER else 'Fail'}")

    if not OVERALL_CLIENT or not OVERALL_SERVER:
        sys.exit(-1)
