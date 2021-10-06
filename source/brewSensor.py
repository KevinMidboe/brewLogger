import bme680
import adafruit_dht
import board
import threading
import time

from logger import logger

class BrewSensor():
    def __init__(self, location, interval=2):
        self.location = location
        self.interval = interval

    @staticmethod
    def getSensorByItsLocation(sensors, location):
        return next(( sensor for sensor in sensors if sensor.location == location), None)


class DHT11Sensor(BrewSensor):
    def __init__(self, pin, location, interval):
        super().__init__(location, interval)
        self.pin = pin
        self.sensor = adafruit_dht.DHT11(board.D17)

    @property
    def temp(self):
        try:
           return self.sensor.temperature
        except RuntimeError as error:
            timeout = 2
            telemetry = {
                'location': self.location,
                'error': str(error),
                'exception': error.__class__.__name__
            }
            logger.error('DHT sensor got invalid checksum, trying again in {} seconds.'.format(timeout), es=telemetry)
            time.sleep(timeout)
            return self.temp

    @property
    def humidity(self):
        return self.sensor.humidity

    def logReadings(self):
        telemetry = {
            'temperature': self.temp,
            'humidity': self.humidity,
            'location': self.location
        }

        logger.info("Sensor readings", es=telemetry)
        return

    def spawnBackgroundSensorLog(self):
        thread = threading.Thread(target=self.logSensorOnIntervalForever, args=())
        thread.daemon = True
        thread.start()
        logger.info("spawned background sensor {} log at interval: {}".format(self.location, self.interval))

    def logSensorOnIntervalForever(self):
        while True:
            try:
                self.logReadings()
            except Exception as error:
                logger.error('Sensor log daemon failed, sleeping and trying again', es={
                    'location': self.location,
                    'error': str(error),
                    'exception': error.__class__.__name__
                })
                time.sleep(2)

            time.sleep(self.interval)

    @staticmethod
    def fromYaml(loader, node):
        return DHT11Sensor(**loader.construct_mapping(node))

class BME680Sensor(BrewSensor):
    def __init__(self, location, interval):
        super().__init__(location, interval)

        self.sensor = bme680.BME680()
        self.sensor.set_humidity_oversample(bme680.OS_2X)
        self.setupSensors()
        self.lastSensorRead = time.time()

    def setupSensors(self):
        self.sensor.set_pressure_oversample(bme680.OS_4X)
        self.sensor.set_temperature_oversample(bme680.OS_8X)
        self.sensor.set_filter(bme680.FILTER_SIZE_3)

        self.sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
        self.sensor.set_gas_heater_temperature(320)
        self.sensor.set_gas_heater_duration(150)
        self.sensor.select_gas_heater_profile(0)

    def read(self):
        self.lastSensorRead = time.time()
        return self.sensor.get_sensor_data()

    def logReadings(self, detailed):
        if self.needToUpdateReadings:
            self.read()

        telemetry = {
            'temperature': self.temp,
            'pressure': self.pressure,
            'humidity': self.humidity,
            'location': self.location
        }

        if detailed:
            telemetry['gasResistance'] = self.gasResistance
            telemetry['stableHeat'] = self.stableHeat

        logger.info("Sensor readings", es=telemetry)
        return

    def saveToFile(self, filename):
        with open(filename, "w") as file:
            file.write("{}".format(self.temp))

    def spawnBackgroundSensorLog(self):
        thread = threading.Thread(target=self.logSensorOnIntervalForever, args=())
        thread.daemon = True
        thread.start()
        logger.info("spawned background sensor {} log at interval: {}".format(self.location, self.interval))

    def logSensorOnIntervalForever(self):
        while True:
            try:
                self.logReadings(detailed=True)
            except Exception as error:
                logger.error('Sensor log daemon failed, sleeping and trying again', es={
                    'location': self.location,
                    'error': str(error),
                    'exception': error.__class__.__name__
                })
                time.sleep(2)

            time.sleep(self.interval)

    @property
    def needToUpdateReadings(self):
        return time.time() - self.lastSensorRead > 1

    @property
    def temp(self):
        if self.needToUpdateReadings:
            self.read()
        return self.sensor.data.temperature

    @property
    def pressure(self):
        if self.needToUpdateReadings:
            self.read()
        return self.sensor.data.pressure

    @property
    def humidity(self):
        if self.needToUpdateReadings:
            self.read()
        return self.sensor.data.humidity

    @property
    def gasResistance(self):
        if self.needToUpdateReadings:
            self.read()
        return self.sensor.data.gas_resistance

    @property
    def stableHeat(self):
        if self.needToUpdateReadings:
            self.read()
        return self.sensor.data.heat_stable

    @staticmethod
    def fromYaml(loader, node):
        return BME680Sensor(**loader.construct_mapping(node))

    def __repr__(self):
        return "{0:.2f} C,{1:.2f} hPa,{2:.2f} %RH".format(self.temp, self.pressure, self.humidity)


if __name__ == '__main__':
#    brewSensor = DHT11Sensor(13, 'outside', 30)
    brewSensor = BME680Sensor('inside', 2)

    while True:
        print(brewSensor.temp)
        time.sleep(1)

