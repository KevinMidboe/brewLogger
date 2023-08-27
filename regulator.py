import time
import threading
from datetime import datetime, timedelta

# local packages
import source
import commandlineArguments
args = commandlineArguments.parse()
import loader as loader
from brewSensor import BrewSensor
from brewRelay import BrewRelay

from logger import logger

'''
We want to also track the time heating and cooling
time delta pr scale unit.

NOTES

This is not realtime critical so to limit interaction with sensor
we pool it on a interval and save it as `currentTemp`.

'''

class BrewRegulator():
  def __init__(self, temperatureSensor, coolingRelay, heatRelay, temperatureGoal, degreesAllowedToDrift, poolingInterval=60):
    self.currentTemp = 0
    self.poolingInterval = poolingInterval
    self.cooling = coolingRelay
    self.heating = heatRelay
    self.temperatureSensor = temperatureSensor
    self.temperatureGoal = temperatureGoal
    self.degreesAllowedToDrift = degreesAllowedToDrift

    self.secondsToDriftSingleDegree = 600

    self.poolTemperatureSensorThread = threading.Thread(target=self.poolTemperatureSensorOnInterval, args=())
    self.poolTemperatureSensorThread.daemon = True

  def poolTemperatureSensorOnInterval(self):
    logger.info('Starting thread pooling temperature sensor', es={ 'timeout': self.poolingInterval })
    while True:
      self.currentTemp = self.temperatureSensor.temp;
      time.sleep(self.poolingInterval);

  def waitForTempReading(self):
    while self.currentTemp == 0:
      time.sleep(0.5)

  @property
  def withinDeviationLimit(self):
    return abs(self.temperatureGoal - self.currentTemp) < self.degreesAllowedToDrift

  @property
  def hasMetTemperatureGoal(self):
    # Given state check if we are still chasing or goal is met.
    if self.state == 'cooling' and self.shouldCool:
      return False
    elif self.state == 'heating' and self.shouldHeat:
      return False

    return True

  @property
  def state(self):
    if self.heating.state is True:
      return 'heating'
    elif self.cooling.state is True:
      return 'cooling'
    else:
      return 'idle'

  @property
  def shouldCool(self):
    return self.currentTemp > self.temperatureGoal

  @property
  def shouldHeat(self):
    return self.currentTemp < self.temperatureGoal

  def setHeating(self, state):
    # Set heating relay if not already
    if self.heating.state is not state:
      self.heating.set(state)

    # Reset cooling if on
    if self.cooling.state is True:
      self.cooling.set(False)

  def setCooling(self, state):
    # Set cooling relay if not already
    if self.cooling.state is not state:
      self.cooling.set(state)

    # Reset heating if on
    if self.heating.state is True:
      self.heating.set(False)

  def turnOnTemperatureControl(self):
    if self.shouldCool:
      self.setCooling(True)
    elif self.shouldHeat:
      self.setHeating(True)

    logger.info('Updated fridge state', es={ 'state': self.state })

  def turnOffTemperatureControl(self):
    if self.heating.state is True:
      self.heating.set(False)

    if self.cooling.state is True:
      self.cooling.set(False)

    logger.info('Updated fridge state', es={ 'state': self.state })

  def temperatureLossFunction(self):
    # return 6
    return self.degreesAllowedToDrift * self.secondsToDriftSingleDegree

  def sustainTemperature(self):
    timeout = self.temperatureLossFunction()

    logger.info('Sustaining temperature', es={
        'state': self.state,
        'temperature': self.currentTemp,
        'goal': self.temperatureGoal,
        'timeout': timeout
    })

    time.sleep(timeout)

  def chaseTemperature(self):
    isGoalMet = False

    # turns on either heating or cooling relay
    self.turnOnTemperatureControl()

    while not isGoalMet:
      if self.hasMetTemperatureGoal:
        logger.info("Temperature met, idling", es={
          'temperature': self.currentTemp,
          'goal': self.temperatureGoal
        })
        isGoalMet = True

      else:
        logger.info("Chasing temperature goal", es={
            'state': self.state,
            'temperature': self.currentTemp,
            'goal': self.temperatureGoal
        })
        time.sleep(self.poolingInterval)

    # turns of any heating or cooling relay
    self.turnOffTemperatureControl()

  def regulateTemperatureTowardsGoal(self):
    while True:
      if self.withinDeviationLimit:
          self.sustainTemperature()
      else:
          self.chaseTemperature()

RELAYS = []
def gracefullyTurnOffRelays():
  for relay in RELAYS:
    if relay.state is True:
      relay.set(False)

def main():
  temp = args.temp
  limit = args.limit
  interval = args.interval

  externalPeripherals = loader.load('brew.yaml')
  sensors = externalPeripherals['sensors']
  relays = externalPeripherals['relays']

  # Sensor import and background logging
  insideSensor = BrewSensor.getSensorByItsLocation(sensors, 'inside')
  if insideSensor is None:
    raise Exception('Missing inside temperature sensor, nothing to do')

  outsideSensor = BrewSensor.getSensorByItsLocation(sensors, 'outside')
  for sensor in [insideSensor, outsideSensor]:
    sensor.spawnBackgroundSensorLog()

  # Relay import and append to list for gracefull shutdown
  coolingRelay = BrewRelay.getRelayByWhatItControls(relays, 'cooling')
  heatRelay = BrewRelay.getRelayByWhatItControls(relays, 'heating')
  RELAYS.extend([coolingRelay, heatRelay])

  # Regulator takes a inside temp, relays, temp and regulating values
  regulator = BrewRegulator(insideSensor, coolingRelay, heatRelay, temp, limit, interval)
  regulator.poolTemperatureSensorThread.start()
  regulator.waitForTempReading()
  regulator.regulateTemperatureTowardsGoal()

if __name__ == '__main__':
  try:
    main()
  except Exception as error:
    logger.error("Regulator crashed! Turning Off all relays.", es={
      'error': str(error),
      'exception': error.__class__.__name__
    })

    gracefullyTurnOffRelays()
    raise error
  except KeyboardInterrupt as error:
    logger.info("Keyboard interrupt! Turning Off all relays.")

    gracefullyTurnOffRelays()
    raise error
