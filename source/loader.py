import yaml

from brewSensor import BME680Sensor, DHT11Sensor, MockSensor
from brewRelay import BrewRelay

def load(filePath):
  loader = yaml.SafeLoader
  loader.add_constructor('!Relay', BrewRelay.fromYaml)
  loader.add_constructor('!bme680', BME680Sensor.fromYaml)
  loader.add_constructor('!dht11', DHT11Sensor.fromYaml)
  loader.add_constructor('!mockSensor', MockSensor.fromYaml)
  return yaml.load(open(filePath, "rb"), Loader=loader)

