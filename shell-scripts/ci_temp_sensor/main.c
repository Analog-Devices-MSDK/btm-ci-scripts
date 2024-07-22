#include <stdio.h>
#include <stdint.h>
#include <string.h>

#include "i2c.h"
#include "mxc_device.h"
#include "max31889_driver.h"


#define I2C_MASTER MXC_I2C0     ///< I2C instance
#define I2C_FREQ 100000         ///< I2C clock frequency
#define SAMPLE_SIZE 3

int main(void)
{
    int error = E_NO_ERROR;
    float temperature;
    float temperature_sum = 0;

    error = MXC_I2C_Init(I2C_MASTER, 1, 0);
    if (error != E_NO_ERROR) {
        printf("I2C master configure failed with error %i\n", error);
        return error;
    }

    MXC_I2C_SetFrequency(I2C_MASTER, I2C_FREQ);

    max31889_driver_t MAX31889 = MAX31889_Open();

    MAX31889.init(I2C_MASTER, MAX31889_I2C_SLAVE_ADDR0); // init the sensor
    while (1)
    {
        temperature_sum = 0;
        for(int i = 0; i < SAMPLE_SIZE; i++)
        {
            error = MAX31889.read(&temperature);
            if (error != E_NO_ERROR) {
                printf("Sensor read error: %i\n", error);
            } else {
                temperature_sum += temperature;
            }
        // Wait for 1s
            MXC_Delay(100);
        }
        printf("%.1f\n", (double)temperature_sum / SAMPLE_SIZE);
    }
    
    return E_NO_ERROR;
}
