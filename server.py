from flask import Flask, request

import source # take a look in source/__init__.py
import loader as loader
from brewSensor import BrewSensor
from brewRelay import BrewRelay

app = Flask(__name__)

externalPeripherals = loader.load('brew.yaml')
sensors = externalPeripherals['sensors']
relays = externalPeripherals['relays']


# Health and error handling
@app.route('/_health')
def health():
    return 'ok'


@app.errorhandler(404)
def pageNotFound(e):
    return {
        'success': False,
        'message': str(e)
    }, 404


@app.errorhandler(405)
def methodNotFound(e):
    return {
        'success:': False,
        'message': str(e)
    }, 405


# API routes
@app.route('/api/sensors')
def allSensors():
    return {
        'sensors': [sensor.info for sensor in sensors]
    }


@app.route('/api/sensor/<location>')
def getSensor(location):
    sensor = BrewSensor.getSensorByItsLocation(sensors, location)
    if not sensor:
        return {
            'success': False,
            'message': 'sensor {} not found, check /sensors'.format(location)
        }, 404

    return sensor.info


@app.route('/api/relays')
def allRelays():
    return {
        'relays': [relay.info for relay in relays]
    }


@app.route('/api/relay/<location>', methods=['GET', 'POST'])
def relatState(location):
    relay = BrewRelay.getRelayByWhatItControls(relays, location)
    if not relay:
        return {
            'success': False,
            'message': 'relay {} not found, check /relays'.format(location)
        }

    if request.method == 'POST':
        relay.set(not relay.state)

    return relay.info


def relayState():
    tempRelays = [BrewRelay.getRelayByName(relays, 'heating'), BrewRelay.getRelayByName(relays, 'cooling')]

    for relay in tempRelays:
        if relay.state is False:
            continue
        return relay.controls
    return 'idle'


@app.route('/api/regulator')
def regulatorState():
    state = relayState()
    goalTemp = 5

    return {
         'state': state,
         'goal': goalTemp
    }


@app.route('/api/regulator/<goal>', methods=['POST'])
def regulatorGoal(goal):
    #TODO implement
   return True


if __name__ == '__main__':
    app.run(host='0.0.0.0')
