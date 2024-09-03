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
ci_temp_sensor.py

Description: CI Temp sensor CLI

"""
from enum import Enum

import serial

from .resource_manager import ResourceManager


class TempUnit(Enum):
    """TEMP UNIT"""

    CELSIUS = 0
    FARENHEIT = 1
    KELVIN = 2


class CiTempSensor:
    TEMPSENSOR_NAME = "tempsensor"

    def __init__(self) -> None:
        self.resource_manager = ResourceManager()

        if self.TEMPSENSOR_NAME not in self.resource_manager.resources:
            raise AttributeError("No temperature sensor available!")

        sensor_port = self.resource_manager.get_item_value(
            f"{self.TEMPSENSOR_NAME}.console_port"
        )
        sensor_baud = self.resource_manager.get_item_value(
            f"{self.TEMPSENSOR_NAME}.baudrate"
        )
        self.port = serial.Serial(sensor_port, baudrate=sensor_baud, timeout=1)

    @staticmethod
    def celsius_to_farenheit(celsius):
        return (celsius * 9 / 5) + 32

    @staticmethod
    def celsius_to_kelvin(celsius):
        return celsius + 273.15

    def read(self, unit: TempUnit = TempUnit.CELSIUS) -> float:
        """Get temperature in celsius

        Returns
        -------
        float
            Temperature
        """
        # try it a few times sometimes that data is only partially in the buffer
        for _ in range(3):
            temp = self.port.readline().decode("utf-8").strip()
            try:
                temp = float(temp)

                if unit == TempUnit.CELSIUS:
                    return temp

                if unit == TempUnit.FARENHEIT:
                    return self.celsius_to_farenheit(temp)

                if unit == TempUnit.KELVIN:
                    return self.celsius_to_kelvin(temp)
            except TimeoutError:
                print("[red]Timeout Occured![/red]")
            except:
                continue

        return float("NaN")
