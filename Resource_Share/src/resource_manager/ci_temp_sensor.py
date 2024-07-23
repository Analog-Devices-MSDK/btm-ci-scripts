import serial
from .resource_manager import ResourceManager
from enum import Enum


class TempUnit(Enum):
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
        self.port = serial.Serial(sensor_port, baudrate=sensor_baud)

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

            except:
                continue

        return float("NaN")
