# Brew Logger

# Requirements
 - python 3 - Download from https://www.python.org/downloads/.
 - virtualenv -  `pip3 install virtualenv`

# Project setup

**Setup virtual environment**:  
`virtualenv -p python3 env`

**Activate a local virtual environment**:  
`source env/bin/activate`

**Install required project packages**:  
 `python install -r requirements.txt`

# Project functionality

We have two executables `server.py` & `regulator.py`. [API Server](#run-api-server) is a api server for getting connected relays & sensors. [Regulator](#run-regulator) uses a heat- and cooling relay with a internal temperature sensor to chase and sustain a target temperature.

# Configuration

Both `brew.yaml` & `config.yaml` requires configuration for your own environment.

### config.yaml
Requires a elasticsearch database connection using address & api key.

### brew.yaml

Configure your own temperature sensors and relay controlled devices. Using YAML syntax for user-defined initialization of classes we map any yaml keys prefixed with `!` to a python class in e.g. `loader.add_constructor('!bme680', BME680Sensor.fromYaml)`.

An example configuration might be:
```
sensors:
  - !bme680
    location: inside

  - !dht11
    pin: 13
    location: outside

  - !mockSensor
    pin: 0
    location: outside
```

Currently supported temperature sensors are:
 - [DHT11](https://learn.adafruit.com/dht)
 - [BME680](https://learn.adafruit.com/adafruit-bme680-humidity-temperature-barometic-pressure-voc-gas)

Easily extend with your own sensors [by following these instructions]() to add support for others to also use.

# Run API server

Start the webserver by running:
```bash
python server.py
```

# Run regulator

Start regulator by running:

```bash
python regulator.py
```

View activity in kibana on index `brewlogger-*` or local file by adding `--logfile regulator.log` and viewed with `tail -f regulator.log`.

# Local development

For easier local development `--mock` flag can be sent to both server and regulator to negate needing connected sensors & relays.

Note: Use sensor type `!mockSensor` in `brew.yml` config.
