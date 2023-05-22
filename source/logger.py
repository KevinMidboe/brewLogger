#!/bin/usr/python3

import logging
import os
import json
import uuid
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
    self.apiKey = kwargs.get('apiKey')
    self.date = date.today()
    self.sessionID = uuid.uuid4()

    logging.StreamHandler.__init__(self)

  def emit(self, record):
    self.format(record)
    datetimeTemplate = '%Y-%m-%dT%H:%M:%S.%f{}'.format(systemTimezone)
    timestamp = datetime.fromtimestamp(record.created).strftime(datetimeTemplate)

    indexURL = 'http://{}:{}/{}-{}/_doc'.format(self.host, self.port, LOGGER_NAME, self.date.strftime('%Y.%m'))
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
    response = urllib.request.urlopen(req)
    response = response.read().decode('utf8')
    return response

class ElasticFieldParameterAdapter(logging.LoggerAdapter):
  def __init__(self, logger, extra={}):
    super().__init__(logger, extra)

  def process(self, msg, kwargs):
    if kwargs == {}:
      return (msg, kwargs)
    extra = kwargs.get("extra", {})
    extra.update({"es": kwargs.pop("es", True)})
    kwargs["extra"] = extra
    return (msg, kwargs)

logger = logging.getLogger(LOGGER_NAME)
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.WARNING)

esHost = config['elastic']['host']
esPort = config['elastic']['port']
esApiKey = config['elastic']['api_key']
eh = ESHandler(host=esHost, port=esPort, apiKey=esApiKey)
eh.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s %(levelname)8s | %(message)s')
logger.addHandler(ch)
logger.addHandler(eh)
logger = ElasticFieldParameterAdapter(logger)
