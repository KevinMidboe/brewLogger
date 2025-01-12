from flask import Flask, request

import source  # take a look in source/__init__.py
import loader as loader
from brewSensor import BrewSensor
from brewRelay import BrewRelay
from database import BrewDatabase

app = Flask(__name__)

externalPeripherals = loader.load('brew.yaml')
sensors = externalPeripherals['sensors']
relays = externalPeripherals['relays']
db = BrewDatabase()
getTargetTemperatureQuery = 'select target_temperature from regulator'


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


@app.route('/api/relay/<name>', methods=['GET', 'POST'])
def relay(name):
    relay = BrewRelay.getRelayByName(relays, name)
    if not relay:
        return {
            'success': False,
            'message': 'relay {} not found, check /relays'.format(name)
        }

    if request.method == 'POST':
        relay.set(not relay.state)

        # toggle the other opposing heating/cooling relay if
        # the other changes. This prevents cooling and
        # heating running at same time by api request
        opposingRelay = BrewRelay.getOppositeRelayByName(relays, name)
        if opposingRelay and opposingRelay.state is True:
            opposingRelay.set(False)

    return relay.info


def relayState():
    tempRelays = [BrewRelay.getRelayByName(
        relays, 'heating'), BrewRelay.getRelayByName(relays, 'cooling')]

    for relay in tempRelays:
        if relay.state is False:
            continue
        return relay.controls
    return 'idle'


@app.route('/api/regulator')
def regulatorState():
    state = relayState()
    goalTemp = db.get(getTargetTemperatureQuery)

    return {
        'state': state,
        'goal': goalTemp
    }


@app.route('/api/regulator/<goal>', methods=['POST'])
def regulatorGoal(goal):
    query = 'update regulator set target_temperature = {}'
    query = query.format(goal)
    success = db.write(query)

    if not success:
        return {
            'success': False,
            'message': 'unable to set target temperature'
        }, 500

    return {
        'success': True,
        'message': 'set target temperature to {}'.format(goal)
    }


if __name__ == '__main__':
    app.run(host='0.0.0.0')
