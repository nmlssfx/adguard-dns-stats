import logging
import requests
from datetime import timedelta
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.core import HomeAssistant
from .const import DOMAIN, BASE_URL, CONF_API_KEY, SCAN_INTERVAL_DEFAULT

_LOGGER = logging.getLogger(__name__)

async def async_setup(hass: HomeAssistant, config: dict):
    if DOMAIN not in config:
        return True

    conf = config[DOMAIN]
    api_key = conf.get(CONF_API_KEY)
    
    # Store the API coordinator in hass.data
    hass.data[DOMAIN] = AdGuardDNSCoordinator(hass, api_key)
    
    # Trigger initial fetch
    await hass.async_add_executor_job(hass.data[DOMAIN].update)
    
    return True

class AdGuardDNSCoordinator:
    def __init__(self, hass, api_key):
        self.hass = hass
        self.api_key = api_key
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
            for item in domains_data.get('stats', [])[:10]:
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
