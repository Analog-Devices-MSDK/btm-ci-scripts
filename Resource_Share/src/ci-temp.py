from resource_manager.ci_temp_sensor import CiTempSensor


def main():
    sensor = CiTempSensor()
    print(sensor.read())

if __name__ == "__main__":
    main()
