import threading
import time
from random import uniform

from logger import logger

class BrewSensor():
    def __init__(self, location, interval=2):
        self.location = location
        self.interval = interval
        self.thread = None

    def spawnBackgroundSensorLog(self):
        self.thread = threading.Thread(target=self.logSensorOnIntervalForever, args=())
        self.thread.daemon = True
        self.thread.start()
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
    def getSensorByItsLocation(sensors, location):
        return next(( sensor for sensor in sensors if sensor.location == location), None)

    @property
    def info(self):
        data = {
            'location': self.location,
            'temperature': "{0:.2f}".format(self.temp),
            'temperature_unit': "°C"
        }

        if hasattr(self, 'humidity'):
            data['humidity'] = "{0:.2f}".format(self.humidity)
            data['humidity_unit'] = "%RH"

        if hasattr(self, 'pressure'):
            data['pressure'] = "{0:.2f}".format(self.pressure)
            data['pressure_unit'] = "bar"

        return data

class BME680Sensor(BrewSensor):
    def __init__(self, location, interval):
        import bme680

        super().__init__(location, interval)

        self.setupSensors()
        self.lastSensorRead = time.time()

    def setupSensors(self):
        try:
            self.sensor = bme680.BME680()
            self.sensor.set_humidity_oversample(bme680.OS_2X)
            self.sensor.set_pressure_oversample(bme680.OS_4X)
            self.sensor.set_temperature_oversample(bme680.OS_8X)
            self.sensor.set_filter(bme680.FILTER_SIZE_3)

            self.sensor.set_gas_status(bme680.ENABLE_GAS_MEAS)
            self.sensor.set_gas_heater_temperature(320)
            self.sensor.set_gas_heater_duration(150)
            self.sensor.select_gas_heater_profile(0)
        except RuntimeError as error:
            logger.error('Sensor not found!', es={
                'location': self.location,
                'error': str(error),
                'exception': error.__class__.__name__
            })

    def read(self):
        self.lastSensorRead = time.time()
        return self.sensor.get_sensor_data()

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

    @staticmethod
    def fromYaml(loader, node):
        return BME680Sensor(**loader.construct_mapping(node))

    def __repr__(self):
        return "{0:.2f} C,{1:.2f} hPa,{2:.2f} %RH".format(self.temp, self.pressure, self.humidity)

class DHT11Sensor(BrewSensor):
    def __init__(self, pin, location, interval):
        import adafruit_dht
        import board

        super().__init__(location, interval)
        self.pin = pin
        self.temperature = 0
        self.sensor = adafruit_dht.DHT11(board.D17, use_pulseio=False)

    @property
    def temp(self):
        try:
            self.temperature = self.sensor.temperature or self.temperature
            return self.temperature
        except RuntimeError as error:
            telemetry = {
                'location': self.location,
                'error': str(error),
                'exception': error.__class__.__name__,
                'temp': self.temperature
            }
            logger.error('DHT sensor got invalid checksum, returning last value.', es=telemetry)
            return self.temperature

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

    @staticmethod
    def fromYaml(loader, node):
        return DHT11Sensor(**loader.construct_mapping(node))

class MockSensor(BrewSensor):
    def __init__(self, pin, location, interval):
        super().__init__(location, interval)
        self.pin = pin
        self.lastTemp = 0

    @property
    def temp(self):
        temp = self.lastTemp + uniform(-0.25, 0.25)

        if self.location == 'inside':
            if temp > 10 or temp < 2:
                temp = 5
        else:
            if temp > 23 or temp < 19:
                temp = 21

        self.lastTemp = temp
        return temp

    @property
    def humidity(self):
        return uniform(80, 99)

    def logReadings(self):
        telemetry = {
            'temperature': self.temp,
            'humidity': self.humidity,
            'location': self.location
        }

        logger.info("Sensor readings", es=telemetry)
        return

    @staticmethod
    def fromYaml(loader, node):
        return MockSensor(**loader.construct_mapping(node))
