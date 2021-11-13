import time
import threading
from datetime import datetime, timedelta

# local packages
import source
from logger import logger

'''
We want to also track the time heating and cooling
time delta pr scale unit.


When we pool:
 Temp too high, if relay is:
  - on  --> keep off
  - off --> turn off
 Temp too low, if relay is:
  - on  --> keep on
  - off --> turn on

 Relay is on, temp is:
  - low  --> keep on
  - high --> turn off
 relay is off, temp is:
  - low  --> keep off
  - high --> turn on
'''

class BrewRegulator():
  def __init__(self, temperatureSensor, coldRelay, hotRelay, temperatureGoal, degreesAllowedToDrift, interval=60, cooldown=600):
    self.interval = interval
    self.cooldown = cooldown
    self.nextStateChangeAfter = datetime.now()

    self.isGoalMet = False
    self.state = 'heating'
    self.cooling = coldRelay
    self.heating = hotRelay
    self.temperatureSensor = temperatureSensor
    self.temperatureGoal = temperatureGoal
    self.degreesAllowedToDrift = degreesAllowedToDrift

    self.secondsToDriftSingleDegree = 600

    self.thread = threading.Thread(target=self.captureOnIntervalForever, args=())
    self.thread.daemon = True

  def start(self):
    self.thread.start()

  '''
  states: heating | cooling | idle
  regulation technique: correction | goal based

  We get a new goal: 18 deg

  Blackbox state() --> Read sensor and decide
  If blackboxState is not current state:
  update regulation tech.


  Get cooldown time based on delta and histogram for temperature interval
  '''

  @property
  def withinDeviationLimit(self):
    return abs(self.temperatureGoal - self.currentTemp) < self.degreesAllowedToDrift

  def checkGoal(self):
    if self.state == 'cooling' and self.currentTemp <= self.temperatureGoal:
      return True
    elif self.state == 'heating' and self.currentTemp >= self.temperatureGoal:
      return True

    return False

  @property
  def shouldCool(self):
    return self.currentTemp > self.temperatureGoal

  @property
  def shouldHeat(self):
    return self.currentTemp < self.temperatureGoal

  def sleepRelativToOffset(self):
    diff = abs(self.temperatureGoal - self.currentTemp)
    temperatureRelativeTimeout = self.interval * diff
    print('sleeping: {}, diff: {}'.format(temperatureRelativeTimeout, diff))
    time.sleep(temperatureRelativeTimeout)

  def chaseTemperature(self):
    isGoalMet = False
    if self.shouldCool:
      self.setCooling()
    elif self.shouldHeat:
      self.setHeating()

    while not isGoalMet:
      self.readAndPrint()

      if not self.checkGoal():
        print("Chasing goal, but sleeping")
        time.sleep(5)
      else:
        print("Temperature met, turning all off and returning")
        isGoalMet = True
        if self.state == 'cooling':
          self.cooling.set(False)
        elif self.state == 'heating':
          self.heating.set(False)

  def temperatureLossFunction(self):
    return self.degreesAllowedToDrift * self.secondsToDriftSingleDegree

  def sustainTemperature(self):
    print('Sustaining temperature')
    self.readAndPrint()

    if self.currentTemp < self.temperatureGoal - self.degreesAllowedToDrift:
      self.cooling.set(True)
      coolingProperty = 30
      print('Cooling turned on! Turning off in {} seconds'.format(coolingProperty))
      time.sleep(coolingProperty)
      self.cooling.set(False)
      print('Cooling turned off')

    elif self.currentTemp > self.temperatureGoal + self.degreesAllowedToDrift:
      self.heating.set(True)
      heatingProperty = 120
      print('Heating turned on! Turning off in {} seconds'.format(heatingProperty))
      time.sleep(heatingProperty)
      self.heating.set(False)
      print('Heating turned off')

    estimatedTimeout = self.temperatureLossFunction()
    print('Allowed drift {}, estimated timeout: {}'.format(self.degreesAllowedToDrift, estimatedTimeout))
    time.sleep(estimatedTimeout)


  def setCooling(self):
    print('should cool')
    self.state = 'cooling'
    self.heating.set(False)
    self.cooling.set(True)

  def setHeating(self):
    print('should heat')
    self.state = 'heating'
    self.heating.set(True)
    self.cooling.set(False)

  def readAndPrint(self):
    self.currentTemp = self.temperatureSensor.temp
    print('current temp: {}, goal: {}'.format(self.currentTemp, self.temperatureGoal))
    print('cold state:', self.cooling.state)
    print('hot state:', self.heating.state)

  def poolSensorAndSetRelay(self):
    self.readAndPrint()
    if not self.withinDeviationLimit:
        self.chaseTemperature()
    else:
        self.sustainTemperature()

  def captureOnIntervalForever(self):
    try:
      while True:
        self.poolSensorAndSetRelay()

        print('sleeping {}'.format(self.interval))
        print('- - - - -')
        time.sleep(self.interval)
    except Error as error:
      logger.error('Regulator crashed!', es={
        'error': str(error),
        'exception': error.__class__.__name__
      })


if __name__ == '__main__':
    import source
    import source.loader as loader
    from source.brewSensor import BrewSensor
    from source.brewRelay import BrewRelay

    externalPeripherals = loader.load('brew.yaml')
    sensors = externalPeripherals['sensors']
    relays = externalPeripherals['relays']

    insideSensor = BrewSensor.getSensorByItsLocation(sensors, 'inside')

    coldRelay = BrewRelay.getRelayByWhatItControls(relays, 'cooling')
    hotRelay = BrewRelay.getRelayByWhatItControls(relays, 'heating')

    regulator = BrewRegulator(insideSensor, coldRelay, hotRelay, 18, 0.5, 10, 60)
    regulator.captureOnIntervalForever()

