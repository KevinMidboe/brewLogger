from __init__ import mock

from logger import logger
from database import BrewDatabase

db = BrewDatabase()

try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError as error:
    if mock == True:
        logger.warning('GPIO module not found, running with mock sensors.\n')
        from mockGPIO import MockGPIO as GPIO
        pass
    else:
        logger.error(
            'GPIO module not found, install or run program with flag --mock argument!\n')
        raise error


class BrewRelay():
    def __init__(self, pin, controls):
        GPIO.setmode(GPIO.BCM)
        self.pin = pin
        self.controls = controls

        self.addIfMissingFromDB()

        GPIO.setup(self.pin, GPIO.OUT)
        self.set(self.state, True)

    @property
    def state(self):
        query = 'select state from relay where pin = {}'.format(self.pin)

        value = db.get(query)
        if value is None:
            return False

        return True if value == 1 else False

    @property
    def info(self):
        return {
            'controls': self.controls,
            'pin': self.pin,
            'state': self.state
        }

    def saveStateToDB(self, state):
        query = 'update relay set state = {} where pin = {}'
        query = query.format(state, self.pin)
        db.write(query)

    def set(self, state, setup=False):
        GPIO.output(self.pin, not state)  # for some reason this is negated
        if setup is False:
            logger.info('Relay toggled', es={
                        'relayState': state, 'relayType': self.controls})
        else:
            logger.info('Resuming relay state', es={
                        'relayState': state, 'relayType': self.controls})

        self.saveStateToDB(state)

    def toggle(self):
        self.set(not state)

    def addIfMissingFromDB(self):
        query = 'select state from relay where pin = {}'
        query = query.format(self.pin)
        value = db.get(query)
        if value is not None:
            return

        query = 'insert into relay (pin, state, controls) values ({}, {}, "{}")'
        query = query.format(self.pin, self.state, self.controls)
        db.write(query)

    @staticmethod
    def fromYaml(loader, node):
        return BrewRelay(**loader.construct_mapping(node))

    @staticmethod
    def getOppositeRelayByName(relays, name):
        oppositeRelayName = None
        if name == 'heating':
            oppositeRelayName = 'cooling'
        elif name == 'cooling':
            oppositeRelayName = 'heating'

        return next((relay for relay in relays if relay.controls == oppositeRelayName), None)

    @staticmethod
    def getRelayByName(relays, controls):
        return next((relay for relay in relays if relay.controls == controls), None)

    def __exit__(self):
        self.conn.close()
