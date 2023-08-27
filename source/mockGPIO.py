
class MockGPIO():
  def __init__(self):
    return

  @property
  def BOARD():
    return True

  @property
  def BCM():
    return True

  @property
  def OUT():
    return True

  def setmode(type):
    return

  def setup(pin, direction):
    return

  def output(pin, state):
    return
