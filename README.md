# brewLogger

## Requirements
 - python 3 - Download from https://www.python.org/downloads/.
 - virtualenv -  `pip3 install virtualenv`

## Setup project

**Setup virtual environment**:  
`virtualenv -p python3 env`

**Activate a local virtual environment**:  
`source env/bin/activate`

**Install required project packages**:  
 `python install -r requirements.txt`

## Run webserver
Start webpage to view sensor & control relays:   
`python3 server.py`

If want to also spawn background threads collecting and pushing log data add the flag `-c`:   
`python3 server.py -c`


## blalblabla
This project uses `brew.yaml` to define all temperature sensors and relay controlled devices. Currently supported temperature sensors are: 
 - [DHT11](https://learn.adafruit.com/dht)
 - [BME680](https://learn.adafruit.com/adafruit-bme680-humidity-temperature-barometic-pressure-voc-gas)

Using YAML syntax for user-defined initialization of classes we map any yaml keys prefixed with "!" to a python class in e.g. `loader.add_constructor('!bme680', BME680Sensor.fromYaml)`.
