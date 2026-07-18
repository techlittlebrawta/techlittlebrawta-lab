# Original Splunk TA-Veracode add-on

The original `splunk/` tree is preserved byte-for-byte from the former
`securitylab` repository. The working add-on is under
`add-ons/TA-veracode/`.

## Behavior

The scripted input:

1. Authenticates to Veracode with `veracode-api-signing`.
2. Retrieves all applications and findings with the Veracode REST APIs.
3. Writes one formatted JSON file per application beneath
   `/opt/splunk/etc/apps/TA-veracode/data/`.
4. Relies on an enabled Splunk batch input to index and delete those files with
   `move_policy = sinkhole`.

The original `local/inputs.conf` runs the script daily at 22:00 and enables both
the script and batch input. It writes events to the `veracode` index with the
`veracode:application:findings` sourcetype.

## Requirements

- Splunk installed at `/opt/splunk`, because the Python path is hard-coded.
- Python 3 available to Splunk.
- Python packages `requests` and `veracode-api-signing` available to the script.
- Veracode API credentials configured for the Splunk service account according
  to the signing library's supported credential mechanism.
- A Splunk index named `veracode`.
- Write access for the Splunk service account to the add-on's `data` directory.

## Deployment review

Do not copy the migrated add-on blindly into production. Its `local`
configuration is enabled and environment-specific. First make a working copy
outside this folder, review the schedule, index, filesystem path, permissions,
retention, and credential placement, then deploy the reviewed copy as
`$SPLUNK_HOME/etc/apps/TA-veracode`.

Useful checks on a Splunk host include:

```sh
$SPLUNK_HOME/bin/splunk btool inputs list --app=TA-veracode --debug
$SPLUNK_HOME/bin/splunk btool props list veracode:application:findings --debug
```

## Known risks and limitations

- HTTP requests have no timeout.
- A connection failure before a response is assigned can trigger an additional
  error while the exception handler reads `response.status_code`.
- Pagination URLs returned by the service are followed without host validation.
- Findings are written to temporary JSON files before Splunk consumes them.
- The enabled batch input deletes consumed JSON files.
- The JSON array format depends on the configured line-breaking expressions.
- There are no source tests, checkpoint, dry-run mode, or automatic rollback.

## Validation and recovery

Use a non-production Splunk test instance and a least-privilege Veracode API
account. Run the script as the Splunk service account, confirm JSON files are
created, then confirm expected events appear in the `veracode` index.

To stop collection, disable both stanzas in the working copy of `inputs.conf`
and restart or reload Splunk as required. Preserve any unindexed JSON before
removing the add-on. Restore the previous app directory or Splunk deployment
package to roll back.
