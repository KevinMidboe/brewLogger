from __init__ import mock

from logger import logger
from utils import getConfig
import sqlite3

lock = threading.Lock()

try:
    import RPi.GPIO as GPIO
except ModuleNotFoundError as error:
    logger.error('GPIO module not found, install or run program with flag --mock argument!\n')
    if mock == True:
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
        self.addIfMissingFromDB()

        GPIO.setup(self.pin, GPIO.OUT)
        self.set(self.state, True)

    @property
    def state(self):
        query = 'select state from relay where pin = {}'.format(self.pin) 

        try:
            lock.acquire(True)
            self.cur.execute(query)
            value = self.cur.fetchone()

            if value is None:
                return False

            return True if value[0] == 1 else False
        except Exception as err:
            logger.error("Error while getting relay state from db")
            logger.error(str(err))
            return False
        finally:
            lock.release()

    @property
    def info(self):
        return {
            'controls': self.controls,
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

    def addIfMissingFromDB(self):
        query = 'select state from relay where pin = {}'
        self.cur.execute(query.format(self.pin))
        if self.cur.fetchone() is not None:
            return

        query = 'insert into relay (pin, state, controls) values ({}, {}, "{}")'
        self.cur.execute(query.format(self.pin, self.state, self.controls))
        self.conn.commit()

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

