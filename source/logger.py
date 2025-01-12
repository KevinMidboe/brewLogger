#!/bin/usr/python3

import logging
import os
import json
import uuid
import argparse
from datetime import datetime, date
import urllib.request

from utils import getConfig, timezoneOffset

config = getConfig()
LOGGER_NAME = config['logger']['name']
systemTimezone = timezoneOffset()

class ESHandler(logging.Handler):
  def __init__(self, *args, **kwargs):
    self.host = kwargs.get('host')
    self.port = kwargs.get('port') or 9200
    self.ssl = kwargs.get('ssl') or True
    self.apiKey = kwargs.get('apiKey')
    self.date = date.today()
    self.sessionID = uuid.uuid4()

    logging.StreamHandler.__init__(self)

  def emit(self, record):
    self.format(record)
    datetimeTemplate = '%Y-%m-%dT%H:%M:%S.%f{}'.format(systemTimezone)
    timestamp = datetime.fromtimestamp(record.created).strftime(datetimeTemplate)

    protocol = 'https' if self.ssl else 'http'
    indexURL = '{}://{}:{}/{}-{}/_doc'.format(protocol, self.host, self.port, LOGGER_NAME, self.date.strftime('%Y.%m'))
    headers = { 'Content-Type': 'application/json', 'User-Agent': 'brewpi-server' }

    if self.apiKey:
      headers['Authorization'] = 'ApiKey {}'.format(self.apiKey)

    doc = {
      'severity': record.levelname,
      'message': record.message,
      '@timestamp': timestamp,
      'sessionID': str(self.sessionID)
    }

    if hasattr(record, 'es'):
      for param in record.es.values():
        if ': {}'.format(param) in record.message:
          doc['message'] = record.message.replace(': {}'.format(str(param)), '')

      doc = {**record.es, **doc}

    payload = json.dumps(doc).encode('utf8')
    req = urllib.request.Request(indexURL, data=payload, headers=headers)
    response = None
    response = urllib.request.urlopen(req)
    response = response.read().decode('utf8')
    return response

class ElasticFieldParameterAdapter(logging.LoggerAdapter):
  def __init__(self, logger: logging.LogRecord, extra={}):
    super().__init__(logger, extra)

  def process(self, msg, kwargs):
    if kwargs == {}:
      return (msg, kwargs)
    extra = kwargs.get("extra", {})
    extra.update({"es": kwargs.pop("es", True)})
    kwargs["extra"] = extra
    return (msg, kwargs)

class ElasticOptionalFormatter(logging.Formatter):
  def format(self, record: logging.LogRecord) -> str:
    # Check if the parameter is present in the log record
    if hasattr(record, 'es'):
      # Format the log message with the parameter
      record.msg = f'{record.msg} | {record.es}'
    return super().format(record)

# General logger setup
formatter = ElasticOptionalFormatter('%(asctime)s | %(levelname)2s | %(message)s')
logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(logging.DEBUG)

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument('--logfile', type=argparse.FileType('w'))
parser.add_argument('--debug', action='store_true')
[args, kwargs] = parser.parse_known_args()

# Stream handler
ch = logging.StreamHandler()
ch.setLevel(logging.WARNING)
ch.setFormatter(formatter)
logger.addHandler(ch)
if args.debug:
  ch.setLevel(logging.DEBUG)

# File handler
if args.logfile:
  fh = logging.FileHandler(args.logfile.name, mode='a', encoding='utf-8')
  fh.setFormatter(formatter)
  logger.addHandler(fh)

# Elastic handler
if config['elastic']['enabled']:
  esHost = config['elastic']['host']
  esPort = config['elastic']['port']
  esApiKey = config['elastic']['api_key']
  esSsl = config['elastic']['ssl']

  eh = ESHandler(host=esHost, port=esPort, apiKey=esApiKey, ssl=esSsl)

  logger.addHandler(eh)

logger = ElasticFieldParameterAdapter(logger)
