import logging
import requests
import json
import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from .const import DOMAIN, BASE_URL, CONF_API_KEY, CONF_SCAN_INTERVAL, CONF_TOP_COUNT, CONF_THEME, SCAN_INTERVAL_DEFAULT

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_API_KEY): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=SCAN_INTERVAL_DEFAULT): cv.positive_int,
        vol.Optional(CONF_TOP_COUNT, default=10): cv.positive_int,
        vol.Optional(CONF_THEME, default="system"): cv.string,
    })
}, extra=vol.ALLOW_EXTRA)

async def async_setup(hass: HomeAssistant, config: dict):
    if DOMAIN in config:
        data = config[DOMAIN]
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": "import"},
                data=data,
            )
        )
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    api_key = entry.data.get(CONF_API_KEY) or entry.options.get(CONF_API_KEY)
    scan_interval = entry.options.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL_DEFAULT)
    top_count = entry.options.get(CONF_TOP_COUNT, 10)
    theme = entry.options.get(CONF_THEME, "system")
    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    coordinator = AdGuardDNSCoordinator(hass, api_key, scan_interval, top_count, theme)
    hass.data[DOMAIN][entry.entry_id] = coordinator
    await hass.async_add_executor_job(coordinator.update)
    entry.add_update_listener(_update_listener)
    await hass.config_entries.async_forward_entry_setups(entry, [Platform.SENSOR])
    async def _export(call):
        path = call.data.get("path")
        target_entry_id = call.data.get("entry_id", entry.entry_id)
        c = hass.data[DOMAIN].get(target_entry_id)
        payload = {
            "api_key": c.api_key,
            "scan_interval": c.scan_interval,
            "top_count": c.top_count,
            "theme": c.theme,
        }
        def _write():
            with open(path, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        await hass.async_add_executor_job(_write)
    async def _import(call):
        path = call.data.get("path")
        target_entry_id = call.data.get("entry_id", entry.entry_id)
        def _read():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        payload = await hass.async_add_executor_job(_read)
        e = hass.config_entries.async_get_entry(target_entry_id)
        new_data = dict(e.data)
        new_options = dict(e.options)
        if "api_key" in payload:
            new_data[CONF_API_KEY] = payload["api_key"]
        if "scan_interval" in payload:
            new_options[CONF_SCAN_INTERVAL] = int(payload["scan_interval"])
        if "top_count" in payload:
            new_options[CONF_TOP_COUNT] = int(payload["top_count"])
        if "theme" in payload:
            new_options[CONF_THEME] = str(payload["theme"])
        hass.config_entries.async_update_entry(e, data=new_data, options=new_options)
        await hass.config_entries.async_reload(target_entry_id)
    hass.services.async_register(DOMAIN, "export_config", _export)
    hass.services.async_register(DOMAIN, "import_config", _import)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    unloaded = await hass.config_entries.async_unload_platforms(entry, [Platform.SENSOR])
    if unloaded and DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unloaded

async def _update_listener(hass: HomeAssistant, entry: ConfigEntry):
    await hass.config_entries.async_reload(entry.entry_id)

class AdGuardDNSCoordinator:
    def __init__(self, hass, api_key, scan_interval, top_count, theme):
        self.hass = hass
        self.api_key = api_key
        self.scan_interval = scan_interval
        self.top_count = top_count
        self.theme = theme
        self.data = {}
        self.headers = {
            "Authorization": f"ApiKey {api_key}",
            "Content-Type": "application/json"
        }

    def update(self):
        """Fetch data from AdGuard DNS API."""
        try:
            # We fetch stats for the last 24 hours to have a meaningful "total" in HA
            # or we could fetch smaller windows. Let's do 24h for a dashboard vibe.
            import time
            now = int(time.time() * 1000)
            day_ago = now - (24 * 60 * 60 * 1000)
            
            params = {
                "time_from_millis": day_ago,
                "time_to_millis": now
            }

            # 1. Total Stats
            r = requests.get(f"{BASE_URL}/stats/time", headers=self.headers, params=params)
            r.raise_for_status()
            time_data = r.json()
            
            total = 0
            blocked = 0
            for item in time_data.get('stats', []):
                val = item.get('value', {})
                total += val.get('queries', 0)
                blocked += val.get('blocked', 0)
            
            # 2. Top Domains
            r = requests.get(f"{BASE_URL}/stats/domains", headers=self.headers, params=params)
            r.raise_for_status()
            domains_data = r.json()
            
            top_domains = []
            for item in domains_data.get('stats', [])[:self.top_count]:
                top_domains.append({
                    "domain": item.get("domain"),
                    "queries": item.get("value", {}).get("queries", 0)
                })

            self.data = {
                "total_queries": total,
                "blocked_queries": blocked,
                "top_domains": top_domains
            }
            _LOGGER.debug("AdGuard DNS data updated: %s", self.data)
        except Exception as e:
            _LOGGER.error("Error updating AdGuard DNS stats: %s", e)
