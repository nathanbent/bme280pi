#!/usr/bin/env python
# BMEmain Script
# V .5 - MySQL, April 2020
# V 1.0 - InfluxDB, May 2020
# V 1.5 - Modularity, to be called in other programs.  Feb 2021

# Want to do
# Improve readability, improve robustness
import time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

import board
from adafruit_bme280 import basic as adafruit_bme280
i2c = board.I2C()  # uses board.SCL and board.SDA
bme280 = adafruit_bme280.Adafruit_BME280_I2C(i2c)

sensor_host_name = "RaspiTest"
# You can generate a Token from the "Tokens Tab" in the UI
token = "U_O0SpT05ZAqNcuorQme0oIfTbzN6XEpVzwno8wAd1nmSGUDF1k9gKr6yJwj_lwPcpwvq5zDH59qHOPZS3aPCg=="
org = "NGBHL"
bucket = "bme280/autogen"

client = InfluxDBClient(url="http://10.0.0.12:8086", token=token)

time_between_reads = 5
time_between_reads_0 = 0  # For when this file gets imported
start_time = time.time()
built_in_credentials = True
credentials_file = "credentials.txt"


def temp_read():  # read temperature, return float with 3 decimal places
    fake_degrees = bme280.temperature
    bme_degrees = (fake_degrees * 1.8) + 32
    return bme_degrees


def humidity_read():  # read humidity, return float with 3 decimal places
    bme_humidity = bme280.humidity
    return bme_humidity


def press_read():  # read pressure, return float with 3 decimal places
    bme_pascals = bme280.pressure
    return bme_pascals


def credentials_setup():
    global credentials
    global credentials_file
    try:
        with open(credentials_file) as f:
            credentials = f.read().splitlines()
    except OSError:
        credentials_file_open = open(credentials_file, 'w')
        spot = 0
        for value in credentials:
            input_value = input("What is the " + value + " for this program? ")
            credentials[spot] = input_value
            credentials_file_open.write(input_value + '\n')
            spot += 1


def write_to_influx(temperature, humidity, pressure, run_count, run_time, errors_corrected):
    global sensor_host_name
    bme280_data = [
        {
            "measurement": "bme280",
            "tags": {
                "host": sensor_host_name
            },
            "fields": {
                "temperature": float(temperature),
                "humidity": float(humidity),
                "pressure": float(pressure),
                "errorscorrected": float(errors_corrected),
                "readruncount": float(run_count),
                "readruntime": float(run_time)
            }
        }
    ]
    print(run_time)
    print((run_count))
    try:
        write_api = client.write_api(write_options=SYNCHRONOUS)
        write_api.write(bucket, org, bme280_data)

    except:
        print("Error encountered BME, waiting for next pass to try again")


def bme280_check_script():
    global time_between_reads
    bme280.sea_level_pressure = 1013.25
    # This should help to set basic parameters for what to expect to help weed out bad results
    errors_corrected = 0
    run_count = 0
    run_loop = True
    while run_loop is True:

        temp_temp = temp_read()
        temp_humidity = humidity_read()
        temp_pressure = press_read()

        # This should weed out bad results
        # This will make sure that it is run once to establish a baseline, and then scale from there
        if run_count > 5:
            if abs(temp_temp - old_temp) > 500:
                temperature = old_temp
                errors_corrected = errors_corrected + 1  # count errors
            else:
                temperature = temp_temp
                old_temp = temp_temp  # allow for results to scale
            if abs(temp_humidity - old_humidity) > 250:
                humidity = old_humidity
                errors_corrected = errors_corrected + 1
            else:
                humidity = temp_humidity
                old_humidity = humidity
            if abs(temp_pressure - old_pressure) > 100:
                pressure = old_pressure
                errors_corrected = errors_corrected + 1
            else:
                pressure = temp_pressure
                old_pressure = temp_pressure

        else:
            temperature = temp_temp
            old_temp = temp_temp
            humidity = temp_humidity
            old_humidity = temp_humidity
            pressure = temp_pressure
            old_pressure = temp_pressure


        # this section will count how many times the script has run
        # and will then calculate the amount of seconds it has been running

        run_count = run_count + 1
        run_time = time.time() - start_time

        write_to_influx(temperature, humidity, pressure, run_count, run_time, errors_corrected)



        print("\nTemperature: %0.1f F" % temperature)
        print("Humidity: %0.1f %%" % humidity)
        print("Pressure: %0.1f hPa" % pressure)
        print("Run count: %0.1f" % run_count)
        print("Run time: %0.1f" % run_time)
        print("Errors Corrected: %0.1f" % errors_corrected)
        # print("Altitude = %0.2f meters" % bme280.altitude)
        if __name__ == "__main__":
            time.sleep(60 * time_between_reads)
        else:
            run_loop = False
            return temperature, humidity

def bme_main():
    bme280_check_script()


def main():
    bme_main()


if __name__ == "__main__":
    main()