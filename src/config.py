"""
Configuration handling of the integration driver.

:copyright: (c) 2023 by Unfolded Circle ApS.
:license: Mozilla Public License Version 2.0, see LICENSE for more details.
"""

import dataclasses
import json
import logging
import os
from dataclasses import dataclass
from typing import Iterator, Callable

from ucapi import EntityTypes

_LOG = logging.getLogger(__name__)

_CFG_FILENAME = "config.json"


def create_entity_id(device_id: str, entity_type: EntityTypes) -> str:
    """Create a unique entity identifier for the given receiver and entity type."""
    return f"{entity_type.value}.{device_id}"


def device_from_entity_id(entity_id: str) -> str | None:
    """
    Return the avr_id prefix of an entity_id.

    The prefix is the part before the first dot in the name and refers to the AVR device identifier.

    :param entity_id: the entity identifier
    :return: the device prefix, or None if entity_id doesn't contain a dot
    """
    return entity_id.split(".", 1)[1]


@dataclass
class DeviceInstance:
    """Orange TV device configuration."""

    id: str
    name: str
    address: str
    always_on: bool

    def __init__(self, id, name, address, always_on):
        self.id = id
        self.name = name
        self.address = address
        self.always_on = always_on


class _EnhancedJSONEncoder(json.JSONEncoder):
    """Python dataclass json encoder."""

    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


class Devices:
    """Integration driver configuration class. Manages all configured Sony devices."""

    def __init__(self, data_path: str,
                 add_handler: Callable[[DeviceInstance], None],
                 remove_handler: Callable[[DeviceInstance|None], None],
                 update_handler: Callable[[DeviceInstance], None]):
        """
        Create a configuration instance for the given configuration path.

        :param data_path: configuration path for the configuration file and client device certificates.
        """
        self._data_path: str = data_path
        self._cfg_file_path: str = os.path.join(data_path, _CFG_FILENAME)
        self._config: list[DeviceInstance] = []
        self._add_handler = add_handler
        self._remove_handler = remove_handler
        self._update_handler = update_handler
        self.load()

    @property
    def data_path(self) -> str:
        """Return the configuration path."""
        return self._data_path

    def all(self) -> Iterator[DeviceInstance]:
        """Get an iterator for all device configurations."""
        return iter(self._config)

    def contains(self, avr_id: str) -> bool:
        """Check if there's a device with the given device identifier."""
        for item in self._config:
            if item.id == avr_id:
                return True
        return False

    def get_by_id_or_address(self, unique_id: str, address: str) -> DeviceInstance | None:
        """
        Get device configuration for a matching id or address.

        :return: A copy of the device configuration or None if not found.
        """
        for item in self._config:
            if item.id == unique_id or item.address == address:
                # return a copy
                return dataclasses.replace(item)
        return None

    def add(self, atv: DeviceInstance) -> None:
        """Add a new configured Sony device."""
        existing = self.get_by_id_or_address(atv.id, atv.address)
        if existing:
            _LOG.debug("Replacing existing device %s => %s", existing, atv)
            self._config.remove(existing)

        self._config.append(atv)
        if self._add_handler is not None:
            self._add_handler(atv)

    def get(self, avr_id: str) -> DeviceInstance | None:
        """Get device configuration for given identifier."""
        for item in self._config:
            if item.id == avr_id:
                # return a copy
                return dataclasses.replace(item)
        return None

    def update(self, device_instance: DeviceInstance) -> bool:
        """Update a configured Sony device and persist configuration."""
        for item in self._config:
            if item.id == device_instance.id:
                item.address = device_instance.address
                item.name = device_instance.name
                item.always_on = device_instance.always_on
                return self.store()
        return False

    def add_or_update(self, atv: DeviceInstance) -> None:
        """Add a new configured device."""
        if self.contains(atv.id):
            _LOG.debug("Existing config %s, updating it %s", atv.id, atv)
            self.update(atv)
            if self._update_handler is not None:
                self._update_handler(atv)
        else:
            _LOG.debug("Adding new config %s", atv)
            self._config.append(atv)
            self.store()
        if self._add_handler is not None:
            self._add_handler(atv)

    def remove(self, device_id: str) -> bool:
        """Remove the given device configuration."""
        device = self.get(device_id)
        if device is None:
            return False
        try:
            self._config.remove(device)
            if self._remove_handler is not None:
                self._remove_handler(device)
            return True
        except ValueError:
            pass
        return False

    def clear(self) -> None:
        """Remove the configuration file."""
        self._config = []

        if os.path.exists(self._cfg_file_path):
            os.remove(self._cfg_file_path)

        if self._remove_handler is not None:
            self._remove_handler(None)

    def store(self) -> bool:
        """
        Store the configuration file.

        :return: True if the configuration could be saved.
        """
        try:
            with open(self._cfg_file_path, "w+", encoding="utf-8") as f:
                json.dump(self._config, f, ensure_ascii=False, cls=_EnhancedJSONEncoder)
            return True
        except OSError:
            _LOG.error("Cannot write the config file")

        return False

    def load(self) -> bool:
        """
        Load the config into the config global variable.

        :return: True if the configuration could be loaded.
        """
        try:
            with open(self._cfg_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                try:
                    self._config.append(DeviceInstance(**item))
                except TypeError as ex:
                    _LOG.warning("Invalid configuration entry will be ignored: %s", ex)
            return True
        except OSError:
            _LOG.error("Cannot open the config file")
        except ValueError:
            _LOG.error("Empty or invalid config file")

        return False


devices: Devices | None = None
