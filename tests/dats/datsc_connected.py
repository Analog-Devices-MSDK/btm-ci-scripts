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
sys.path.append("../..")

# pylint: disable=import-error,wrong-import-position
from Resource_Share.resource_manager import ResourceManager

# pylint: enable=import-error,wrong-import-position


class BasicTester:
    def __init__(self, portname: str) -> None:
        self.portname = portname
        self.text = ""
        self.serial_port = serial.Serial(portname, baudrate=115200, timeout=2)
        self.serial_port.flush()

    def slow_write(self, data: bytes):
        """Write UART data at human typing speeds

        Parameters
        ----------
        serial_port : serial.Serial
            Port to write data to
        data : bytes
            Data to write out
        """
        for byte in data:
            self.serial_port.write(byte)
            time.sleep(0.1)

    def test_secure_connection(self) -> bool:
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

        while True:
            new_text = self.serial_port.read(self.serial_port.in_waiting).decode(
                "utf-8"
            )
            self.text += new_text

            print(new_text, end="")

            # wait until you see the term passkey, so we can enter the pin
            if "passkey" in self.text:
                time.sleep(1)
                self.serial_port.write("pin 1 1234\n".encode("utf-8"))
                break

            if "Connection encrypted" in self.text:
                return True

            if (datetime.now() - start).total_seconds() > 30:
                print("TIMEOUT!!")
                return False

        print("Passkey entered")
        start = datetime.now()
        while True:
            new_text = self.serial_port.read(self.serial_port.in_waiting).decode(
                "utf-8"
            )
            self.text += new_text
            print(new_text, end="")

            # wait for pairing process to go through and see if it passed or failed
            if "Pairing failed" in self.text:
                print("Pairing failed")
                return False

            if (
                "Pairing completed successfully" in self.text
                or "Connection encrypted" in self.text
            ):
                print("Pairing success")
                return True

            

            if (datetime.now() - start).total_seconds() > 30:
                print("TIMEOUT!!")
                return False


class ClientTester(BasicTester):
    def __init__(self, portname: str) -> None:
        BasicTester.__init__(self, portname=portname)

    def write_char_test(self) -> bool:
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

        self.serial_port.write("btn 2 l\n".encode("utf-8"))
        time.sleep(1)
        self.serial_port.write("btn 2 l\n".encode("utf-8"))

        start = datetime.now()

        while True:
            new_text = self.serial_port.read(self.serial_port.in_waiting).decode(
                "utf-8"
            )
            self.text += new_text
            print(new_text, end="")

            if "No action assigned" in self.text:
                return False

            if "hello" in self.text:
                return True

            if (datetime.now() - start).total_seconds() > 10:
                print("TIMEOUT!!")
                return False

            time.sleep(0.5)
            self.serial_port.write("btn 2 l\n".encode("utf-8"))

    def write_secure_test(self) -> bool:
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
        self.serial_port.write("btn 2 m\n".encode("utf-8"))

        start = datetime.now()

        while True:
            new_text = self.serial_port.read(self.serial_port.in_waiting).decode(
                "utf-8"
            )
            self.text += new_text
            print(new_text, end="")

            if "No action assigned" in self.text:
                return False

            if "hello" in self.text or "Secure data received!" in self.text:
                return True
            if (datetime.now() - start).total_seconds() > 10:
                print("TIMEOUT!!")
                return False

            time.sleep(1)
            self.serial_port.write("btn 2 m\r\n".encode("utf-8"))

    def phy_switch_test(self) -> bool:
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

        self.serial_port.write("btn 2 s\n".encode("utf-8"))
        start = datetime.now()

        while True:
            new_text = self.serial_port.read(self.serial_port.in_waiting).decode(
                "utf-8"
            )
            self.text += new_text
            print(new_text, end="")

            if "No action assigned" in self.text:
                return False

            # if "2 MBit TX and RX PHY Requested" in text:
            #     return True
            if "DM_PHY_UPDATE_IND" in self.text:
                return True

            if (datetime.now() - start).total_seconds() > 10:
                print("TIMEOUT!!")
                return False

            time.sleep(0.5)
            self.serial_port.write("btn 2 s\n".encode("utf-8"))

    def _run_speed_test(self):
        pass
        self.serial_port.write("btn 2 x\n".encode("utf-8"))
        time.sleep(1)
        self.serial_port.write("btn 2 m\n".encode("utf-8"))

    def speed_test(self) -> bool:
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

        
        # self._run_speed_test()
        self.slow_write("btn 2 x\n".encode("utf-8"))
        time.sleep(1)
        self.slow_write("btn 2 m\n".encode("utf-8"))

        start = datetime.now()

        while True:
            new_text = self.serial_port.read(self.serial_port.in_waiting).decode(
                "utf-8"
            )
            self.text += new_text
            print(new_text, end="")

            if "bps" in self.text:
                print(self.text)
                return True

            if (datetime.now() - start).total_seconds() > 20:
                print("\nTIMEOUT!!")
                return False
            print('Execute')
            # self._run_speed_test()  
            self.slow_write("btn 2 x\n".encode("utf-8"))
            time.sleep(1)
            self.slow_write("btn 2 m\n".encode("utf-8"))
            


test_results_client = {}


def _client_thread(portname: str, board: str, resource_manager: ResourceManager, owner: str):
    resource_manager.resource_reset(board, owner)

    client = ClientTester(portname)

    test_results_client["pairing"] = client.test_secure_connection()
    if not test_results_client["pairing"]:
        return test_results_client

    test_results_client["write characteristic"] = client.write_char_test()
    test_results_client["write secure"] = client.write_secure_test()
    test_results_client["speed"] = client.speed_test()
    test_results_client["phy switch"] = client.phy_switch_test()

    return test_results_client


test_results_server = {}


def _server_thread(portname: str, board: str, resource_manager: ResourceManager, owner: str):
    server = BasicTester(portname)
    resource_manager.resource_reset(board, owner)
    test_results_server["pairing"] = server.test_secure_connection()

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


def main():
    if len(sys.argv) < 3:
        print("Not enough arguments!")
        sys.exit(-1)

    resource_manager = ResourceManager()

    # Get the boards under test and the file paths
    server_board = sys.argv[1]
    client_board = sys.argv[2]

    # sanity check
    assert (
        server_board != client_board
    ), f"Client Board ({client_board}) must not  be the same as Server ({server_board})"

    # Get console ports associated with the boards
    server_port = resource_manager.get_item_value(f"{server_board}.console_port")
    client_port = resource_manager.get_item_value(f"{client_board}.console_port")

    # Reset to start from scratch
    owner = resource_manager.get_owner(server_board)

    # Configure and run tests
    client_t = threading.Thread(
        target=_client_thread,
        args=(
            client_port,
            server_board,
            resource_manager,
            owner,
        ),
    )
    server_t = threading.Thread(
        target=_server_thread,
        args=(
            server_port,
            client_board,
            resource_manager,
            owner,
        ),
    )

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


if __name__ == "__main__":
    main()
