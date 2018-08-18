"""
Support for Philips Hue sensors, such as the motion sensor
"""
import asyncio
import async_timeout
from homeassistant.components import hue
from homeassistant.const import TEMP_CELSIUS, DEVICE_CLASS_TEMPERATURE, DEVICE_CLASS_HUMIDITY, DEVICE_CLASS_ILLUMINANCE
from homeassistant.helpers.entity import Entity
import logging

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['hue']

ZLL_TEMPERATURE = 'ZLLTemperature'
ZLL_LIGHT_LEVEL = 'ZLLLightLevel'


async def setup_platform(hass, config, add_devices, discovery_info=None):
    """Not needed"""
    pass


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up a Hue sensor based on a config entry."""
    import aiohue

    all_sensors = []

    bridge = hass.data[hue.DOMAIN][entry.data['host']]

    sensors = bridge.api.sensors

    try:
        with async_timeout.timeout(4):
            await sensors.update()
    except (asyncio.TimeoutError, aiohue.AiohueException):
        if not bridge.available:
            return []

        _LOGGER.error('Unable to reach bridge %s', bridge.host)
        bridge.available = False

        return []

    if not bridge.available:
        _LOGGER.info('Reconnected to bridge %s', bridge.host)
        bridge.available = True

    for item_id in sensors:
        sensor = sensors[item_id]
        if sensor.type == ZLL_TEMPERATURE:
            all_sensors.append(HueTemperatureSensor(sensor))
        elif sensor.type == ZLL_LIGHT_LEVEL:
            all_sensors.append(HueLightSensor(sensor))

    async_add_devices(all_sensors)


class HueSensor(Entity):
    """Class to hold Hue Sensor basic info."""

    def __init__(self, sensor):
        self._name = sensor.name
        self._config = sensor.config
        self._state = sensor.state
        self._uuid = sensor.uniqueid

    @property
    def name(self):
        return self._name

    @property
    def unique_id(self):
        """Return a unique ID."""
        return 'hue_sensor.{}'.format(self._uuid)

    def update(self):
        """Retrieve latest state."""
        pass


class HueLightSensor(HueSensor):
    def determine_lux_value(self):
        lightlevel = self._state['lightlevel']
        if lightlevel is not None:
            lux = round(float(10 ** ((lightlevel - 1) / 10000)), 2)
        else:
            lux = 0
        return lux

    @property
    def device_state_attributes(self):
        config = self._config
        state = self._state
        attrs = {
            'lastupdated': state['lastupdated'],
            'daylight': state['daylight'],
            'dark': state['dark'],
            'lightlevel': state['lightlevel'],

            'tholdoffset': config['tholdoffset'],

            'alert': config['alert'],
            'battery': config['battery'],
            'ledindication': config['ledindication'],
            'on': config['on'],
            'reachable': config['reachable'],
            'usertest': config['usertest'],
        }
        return attrs

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.determine_lux_value()

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return 'lx'

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return DEVICE_CLASS_ILLUMINANCE


class HueTemperatureSensor(HueSensor):
    @property
    def device_state_attributes(self):
        config = self._config
        state = self._state
        attrs = {
            'lastupdated': state['lastupdated'],

            'alert': config['alert'],
            'battery': config['battery'],
            'ledindication': config['ledindication'],
            'on': config['on'],
            'reachable': config['reachable'],
            'usertest': config['usertest'],
        }
        return attrs

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state['temperature'] / 100

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return DEVICE_CLASS_TEMPERATURE
