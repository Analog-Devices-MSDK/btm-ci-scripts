import serial
from .resource_manager import ResourceManager
class CiTempSensor:

    TEMPSENSOR_NAME = "tempsensor"

    def __init__(self) -> None:
        self.resource_manager = ResourceManager()

        if self.TEMPSENSOR_NAME not in self.resource_manager.resources:
            raise AttributeError("No temperature sensor available!")
        
        sensor_port = self.resource_manager.get_item_value(f'{self.TEMPSENSOR_NAME}.console_port')
        sensor_baud = self.resource_manager.get_item_value(f'{self.TEMPSENSOR_NAME}.baudrate')
        self.port = serial.Serial(sensor_port,baudrate=sensor_baud)

    def read(self):
        data = self.port.read_all()
        return float(data.split('\n')[-1].strip())
