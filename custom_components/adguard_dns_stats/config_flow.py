import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN, CONF_API_KEY, CONF_SCAN_INTERVAL, CONF_TOP_COUNT, CONF_THEME, SCAN_INTERVAL_DEFAULT

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            api_key = user_input.get(CONF_API_KEY)
            if not api_key:
                errors[CONF_API_KEY] = "invalid"
            else:
                return self.async_create_entry(title="AdGuard DNS Statistics", data={CONF_API_KEY: api_key})
        schema = vol.Schema({vol.Required(CONF_API_KEY): str})
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_import(self, user_input):
        return await self.async_step_user(user_input)

class OptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry):
        self.entry = entry

    async def async_step_init(self, user_input=None):
        return self.async_show_menu(step_id="init", menu_options=["general", "advanced", "appearance"])

    async def async_step_general(self, user_input=None):
        if user_input is not None:
            data = dict(self.entry.options)
            if user_input.get(CONF_API_KEY):
                data[CONF_API_KEY] = user_input.get(CONF_API_KEY)
            return self.async_create_entry(title="General", data=data)
        schema = vol.Schema({vol.Optional(CONF_API_KEY, default=self.entry.data.get(CONF_API_KEY, self.entry.options.get(CONF_API_KEY, ""))): str})
        return self.async_show_form(step_id="general", data_schema=schema)

    async def async_step_advanced(self, user_input=None):
        if user_input is not None:
            data = dict(self.entry.options)
            data[CONF_SCAN_INTERVAL] = int(user_input.get(CONF_SCAN_INTERVAL))
            data[CONF_TOP_COUNT] = int(user_input.get(CONF_TOP_COUNT))
            return self.async_create_entry(title="Advanced", data=data)
        schema = vol.Schema({
            vol.Required(CONF_SCAN_INTERVAL, default=self.entry.options.get(CONF_SCAN_INTERVAL, SCAN_INTERVAL_DEFAULT)): int,
            vol.Required(CONF_TOP_COUNT, default=self.entry.options.get(CONF_TOP_COUNT, 10)): int,
        })
        return self.async_show_form(step_id="advanced", data_schema=schema)

    async def async_step_appearance(self, user_input=None):
        if user_input is not None:
            data = dict(self.entry.options)
            data[CONF_THEME] = user_input.get(CONF_THEME)
            return self.async_create_entry(title="Appearance", data=data)
        schema = vol.Schema({vol.Required(CONF_THEME, default=self.entry.options.get(CONF_THEME, "system")): vol.In(["system", "light", "dark"])})
        return self.async_show_form(step_id="appearance", data_schema=schema)

async def async_get_options_flow(entry):
    return OptionsFlow(entry)