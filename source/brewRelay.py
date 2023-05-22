from __init__ import mock

from logger import logger
from utils import getConfig
import sqlite3

try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError as error:
    if mock is True:
        from mockGPIO import MockGPIO as GPIO
        pass
    else:
        raise error

class BrewRelay():
    def __init__(self, pin, controls):
        GPIO.setmode(GPIO.BCM)
        self.pin = pin
        self.controls = controls

        config = getConfig()
        self.conn = sqlite3.connect(config['database']['name'], check_same_thread=False)
        self.cur = self.conn.cursor()

        GPIO.setup(self.pin, GPIO.OUT)
        self.set(self.state, True)

    @property
    def state(self):
        query = 'select state from relay where pin = {}'.format(self.pin) 
        self.cur.execute(query)

        return True if self.cur.fetchone()[0] == 1 else False

    @property
    def info(self):
        return {
            'location': self.controls,
            'pin': self.pin,
            'state': self.state
        }

    def saveStateToDB(self, state):
        query = 'update relay set state = {} where pin = {}'
        self.cur.execute(query.format(state, self.pin))
        self.conn.commit()

    def set(self, state, setup=False):
        GPIO.output(self.pin, not state) # for some reason this is negated
        if setup is False:
            logger.info('Relay toggled', es={'relayState': state, 'relayType': self.controls})
        else:
            logger.info('Resuming relay state', es={'relayState': state, 'relayType': self.controls})

        self.saveStateToDB(state)

    def toggle(self):
        self.set(not state)

    @staticmethod
    def fromYaml(loader, node):
        return BrewRelay(**loader.construct_mapping(node))

    @staticmethod
    def getRelayByWhatItControls(relays, controls):
        return next(( relay for relay in relays if relay.controls == controls), None)

    @staticmethod
    def getRelayByName(relays, controls):
        return next(( relay for relay in relays if relay.controls == controls), None)

    def __exit__(self):
        self.conn.close()

