import os
import sys
import yaml
from flask import Flask, request, render_template, send_file, redirect, send_from_directory
from brewSensor import BCM600Sensor, DHT11Sensor, BrewSensor
from brewCamera import BrewCamera
from brewRelay import BrewRelay

app = Flask(__name__)
brewCamera = BrewCamera(20)

def readYaml(filePath):
  loader = yaml.SafeLoader
  loader.add_constructor('!Relay', BrewRelay.fromYaml)
  loader.add_constructor('!bcm600', BCM600Sensor.fromYaml)
  loader.add_constructor('!dht11', DHT11Sensor.fromYaml)
  return yaml.load(open(filePath, "rb"), Loader=loader)

rangers = readYaml('brew.yaml')
sensors = rangers['sensors']
relays = rangers['relays']

if sys.argv[-1] == '-c':
    brewCamera.spawnBackgroundCapture()

    for sensor in sensors:
        sensor.spawnBackgroundSensorLog()

def sensorTemp(location):
    sensor = BrewSensor.getSensorByItsLocation(sensors, location)
    if sensor:
        return sensor.temp
    return 'not found :('

@app.route('/toggle/<controls>', methods=['POST', 'GET'])
def toggle(controls):
    if request.method == 'GET':
        return redirect('/')

    relay = BrewRelay.getRelayByWhatItControls(relays, controls)
    if relay:
        relay.set(not relay.state)
        if relay.controls == 'light':
            brewCamera.capture()
    else:
        print('relay {} not found'.format(controls))

    return redirect('/')

@app.route('/assets/<filename>')
def assets(filename):
    return send_file('./assets/{}'.format(filename))

@app.route('/favicon.ico')
def favicon():
    faviconPath = os.path.join(app.root_path, 'assets/favicon')
    return send_from_directory(faviconPath, 'favicon.ico')

@app.route('/feed')
def feed():
    return send_file('./foo.jpg')

@app.route('/')
def index():
    return render_template('./index.html',
            sensors=sensors,
            sensorTemp=sensorTemp,
            relays=relays,
            captureInterval=brewCamera.interval)

if __name__ == '__main__':
    app.run(host='0.0.0.0')