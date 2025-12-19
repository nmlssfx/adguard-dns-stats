# AdGuard DNS Statistics for Home Assistant

A custom Home Assistant integration to track your [AdGuard DNS](https://adguard-dns.io/) statistics.

## Features

- **Total Queries**: Monitoring total DNS requests in the last 24 hours.
- **Blocked Queries**: Monitoring blocked DNS requests in the last 24 hours.
- **Top Domains**: List of the most active domains with itemized statistics available in the sensor attributes.

## Installation

### Via HACS (Recommended)
1. Open HACS in Home Assistant.
2. Click the three dots in the top right corner and select **Custom repositories**.
3. Paste the URL of this repository.
4. Select **Integration** as the category and click **Add**.
5. Find "AdGuard DNS Statistics" in HACS and click **Install**.
6. Restart Home Assistant.

### Manual Installation
1. Download the `custom_components/adguard_dns_stats` folder.
2. Copy it into your Home Assistant's `custom_components` directory.
3. Restart Home Assistant.

## Configuration

Add the following to your `configuration.yaml`:

```yaml
adguard_dns_stats:
  api_key: "YOUR_API_KEY"

sensor:
  - platform: adguard_dns_stats
```

## Dashboard Example (Markdown Card)

```yaml
type: markdown
content: >
  ### Top Domains (Last 24h)
  | Domain | Queries |
  | :--- | :--- |
  {% for item in state_attr('sensor.adguard_dns_top_domains', 'domains') %}
  | {{ item.domain }} | {{ item.queries }} |
  {% endfor %}
```
