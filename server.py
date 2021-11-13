import os
import sys
from flask import Flask, request, render_template, send_file, redirect, send_from_directory

import source # take a look in source/__init__.py
from brewCamera import BrewCamera
from brewSensor import BrewSensor
from brewRelay import BrewRelay
import source.loader as loader

def isItInArgv(it):
    return it in sys.argv

app = Flask(__name__)
brewCamera = BrewCamera(20)

externalPeripherals = loader.load('brew.yaml')
sensors = externalPeripherals['sensors']
relays = externalPeripherals['relays']

if isItInArgv('-d') or isItInArgv('--daemon'):
    brewCamera.spawnBackgroundCapture()

    for sensor in sensors:
        try:
            sensor.spawnBackgroundSensorLog()
        except Error as error:
            print('Error while spawning sensor background task:', error)

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
