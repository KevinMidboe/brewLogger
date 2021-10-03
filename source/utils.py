#!/bin/usr/python3
import os
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

