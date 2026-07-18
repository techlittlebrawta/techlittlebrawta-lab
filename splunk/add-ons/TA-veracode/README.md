# TA-veracode

This Splunk technology add-on collects application findings from the Veracode
REST API. The scripted input writes one compact JSON event per finding to
standard output, which Splunk indexes as `veracode:application:findings`.

This is a community example and is not an official Veracode or Splunk add-on.
Test it in a non-production Splunk environment before deployment.

## Improvements over the migrated prototype

- Fixes an uninitialized-response error during connection failures.
- Adds connection and read timeouts, bounded exponential retries, `Retry-After`
  support, and retries for HTTP 429 and transient server errors.
- Rejects pagination links that leave the official HTTPS Veracode API host.
- Sends logs to standard error so they are not indexed as finding events.
- Emits newline-delimited JSON directly instead of writing temporary JSON files
  and deleting them through a batch input.
- Ships disabled defaults under `default/`; administrators enable or override
  them under `local/`.
- Keeps credentials outside the repository.

## Requirements

- Splunk Enterprise with a Python 3.9 or newer runtime available to scripted inputs
- A Veracode API service account with only the permissions needed to read applications and findings
- A Splunk index named `veracode`, or a site-specific index override
- Outbound HTTPS access to `api.veracode.com`

## Install

Copy the `TA-veracode` directory to:

```text
$SPLUNK_HOME/etc/apps/TA-veracode
```

Install the Python dependencies into the app-local `lib` directory. Run from the
Splunk host and adjust the Splunk service account or path if needed:

```bash
cd "$SPLUNK_HOME/etc/apps/TA-veracode"
python3 -m pip install --target lib --requirement requirements.txt
chown -R splunk:splunk "$SPLUNK_HOME/etc/apps/TA-veracode"
```

The dependency versions are fixed so deployments are repeatable. Review and
test upgrades before changing them.

## Configure Veracode credentials

The Veracode signing library supports a credentials file or environment
variables. Use only one method. A credentials file is usually easier for a
Splunk service account.

Create the file in the Splunk service account's home directory, commonly
`$SPLUNK_HOME/.veracode/credentials`:

```ini
[default]
veracode_api_key_id = REPLACE_WITH_KEY_ID
veracode_api_key_secret = REPLACE_WITH_KEY_SECRET
```

Restrict it to the Splunk account:

```bash
chown splunk:splunk "$SPLUNK_HOME/.veracode/credentials"
chmod 600 "$SPLUNK_HOME/.veracode/credentials"
```

Never store the real key ID or secret in this repository, `inputs.conf`, command
history, or screenshots. Rotate the credentials if they are exposed.

Official credential setup guidance:
[Veracode API authentication](https://docs.veracode.com/r/t_install_api_authen).

## Configure and enable the input

Create the target index first, or change the `index` value below to an existing
approved index. Then create `$SPLUNK_HOME/etc/apps/TA-veracode/local/inputs.conf`:

```ini
[script://$SPLUNK_HOME/etc/apps/TA-veracode/bin/veracode.py]
disabled = false
interval = 0 22 * * *
index = veracode
sourcetype = veracode:application:findings
python.version = python3
```

The example runs every day at 22:00 in the Splunk server's timezone. Change the
five-field cron schedule in the `local` file when a different interval is
required.

Restart Splunk after installing or changing the add-on:

```bash
"$SPLUNK_HOME/bin/splunk" restart
```

## Validate

Run the script as the Splunk service account before enabling the scheduled input:

```bash
sudo -u splunk env HOME="$SPLUNK_HOME" \
  "$SPLUNK_HOME/etc/apps/TA-veracode/bin/veracode.py" > /tmp/veracode-test.ndjson
```

Confirm the command exits successfully and that each output line is one valid
JSON object. Delete the test file after validation because findings can contain
sensitive application details.

Check the effective Splunk configuration:

```bash
"$SPLUNK_HOME/bin/splunk" btool inputs list --app=TA-veracode --debug
"$SPLUNK_HOME/bin/splunk" btool props list veracode:application:findings --debug
```

Search for collected events:

```spl
index=veracode sourcetype=veracode:application:findings
```

Operational logs are written to Splunk's scripted-input logging path because
the script uses standard error for diagnostics.

## Test the Python code

From the add-on directory, with dependencies installed:

```bash
python3 -m unittest discover -s tests -v
```
