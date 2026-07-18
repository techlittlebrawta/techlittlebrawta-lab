# Splunk

This section contains Splunk applications, technology add-ons, and deployment
documentation.

## Contents

- [`add-ons/`](add-ons/) — technology add-ons that collect or normalize data.
- [`apps/`](apps/) — reserved for complete Splunk applications and dashboards.

Never commit Splunk authentication tokens, API secrets, private keys, customer
data, or exported production configuration. Put deployment-specific overrides
under an app's `local/` directory on the Splunk system, not in this repository.
