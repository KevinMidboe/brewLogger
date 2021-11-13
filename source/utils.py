#!/bin/usr/python3
import os
import subprocess
import yaml

def loadYaml(filePath):
  with open(filePath, "r") as stream:
    try:
        return yaml.safe_load(stream)
    except yaml.YAMLError as exception:
        print('Error: {} is unparsable'.format(filePath))
        print(exception)

def getConfig():
  pwd = os.path.dirname(os.path.abspath(__file__))
  path = os.path.join(pwd,'../', 'config.yaml')

  if not os.path.isfile(path):
    print('Please fill out and rename config file. Check README for more info.')
    exit(0)

  return loadYaml(path)

def timezoneOffset():
  localTimezoneCommand = 'date +%z'
  process = subprocess.Popen(localTimezoneCommand.split(), stdout=subprocess.PIPE)
  output, error = process.communicate()

  fallbackTimezone = '+0100'
  if error:
    print('Error when trying to fetch timezone: {}. Returning fallbacktimezone: {}.'.format(error, fallbackTimezone))
    return fallbackTimezone

  try:
    output = output.decode("utf-8")
    if '\n' in output:
      output = output.replace('\n', '')
    return output or fallbackTimezone
  except Error as error:
    print('Error occured while decoding output from system timezone: {}'.format(error))
    return fallbackTimezone

