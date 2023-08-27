import argparse

def parse():
  parser = argparse.ArgumentParser()
  parser.add_argument('temp', type=float, help='Goal temperature')
  parser.add_argument('limit', type=float, help='Temperate deviation limit')
  parser.add_argument('interval', type=int, help='Sensor pooling interval')
  parser.add_argument('--mock', action='store_true', help="Mock peripheral sensors")
  parser.add_argument('--logfile', nargs='?', type=argparse.FileType('w'), help="Write log record to file")
  parser.add_argument('--debug', action='store_true', help="Console log level set to debug ")
  args = parser.parse_args()
  return args