import serial
from .resource_manager import ResourceManager


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

    def read(self) -> float:
        """Get temperature in celsius

        Returns
        -------
        float
            Temperature
        """
        # try it a few times sometimes that data is only partially in the buffer
        for _ in range(3):
            data = self.port.readline().decode("utf-8").strip()
            try:
                data = float(data)
                return data
            except:
                continue

        return float("NaN")
