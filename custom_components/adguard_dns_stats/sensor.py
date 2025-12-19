from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from .const import DOMAIN

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    store = hass.data.get(DOMAIN)
    if isinstance(store, dict) and store:
        coordinator = next(iter(store.values()))
    else:
        coordinator = store
    entities = [
        AdGuardDNSSensor(coordinator, "Total Queries", "total_queries", "mdi:dns"),
        AdGuardDNSSensor(coordinator, "Blocked Queries", "blocked_queries", "mdi:dns-lock"),
        AdGuardDNSTopDomainsSensor(coordinator)
    ]
    async_add_entities(entities, True)

async def async_setup_entry(hass, entry: ConfigEntry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        AdGuardDNSSensor(coordinator, "Total Queries", "total_queries", "mdi:dns"),
        AdGuardDNSSensor(coordinator, "Blocked Queries", "blocked_queries", "mdi:dns-lock"),
        AdGuardDNSTopDomainsSensor(coordinator)
    ]
    async_add_entities(entities, True)

class AdGuardDNSSensor(SensorEntity):
    def __init__(self, coordinator, name, data_key, icon):
        self.coordinator = coordinator
        self._name = f"AdGuard DNS {name}"
        self._data_key = data_key
        self._icon = icon

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self.coordinator.data.get(self._data_key)

    @property
    def icon(self):
        return self._icon

    @property
    def unit_of_measurement(self):
        return "queries"

    def update(self):
        self.coordinator.update()

class AdGuardDNSTopDomainsSensor(SensorEntity):
    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._name = "AdGuard DNS Top Domains"

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        # State is just the first domain
        top = self.coordinator.data.get("top_domains", [])
        if top:
            return top[0]["domain"]
        return "No data"

    @property
    def extra_state_attributes(self):
        return {
            "domains": self.coordinator.data.get("top_domains", [])
        }

    @property
    def icon(self):
        return "mdi:list-status"

    def update(self):
        self.coordinator.update()
