from utils import getConfig
from logger import logger
import sqlite3
import threading


class BrewDatabase():
    def __init__(self):
        config = getConfig()
        self.conn = sqlite3.connect(
            config['database']['name'], check_same_thread=False)
        self.cur = self.conn.cursor()

    def get(self, query):
        try:
            cur = self.conn.cursor()
            cur.execute(query)
            value = cur.fetchone()
            if value is None or len(value) < 1:
                return None

            return value[0]
        except Exception as err:
            logger.error("Error while fetching query from database")
            logger.error(str(err))
            return None

    def getAll(self, query):
        try:
            self.cur.execute(query)
            value = self.cur.fetchall()
            return value
        except Exception as err:
            logger.error("Error while fetching query from database")
            logger.error(str(err))
            return False

    def write(self, query):
        try:
            cur = self.conn.cursor()
            cur.execute(query)
            self.conn.commit()
            return True
        except Exception as err:
            logger.error(str(err))
            logger.error("Error while writing query to database")

            return False
