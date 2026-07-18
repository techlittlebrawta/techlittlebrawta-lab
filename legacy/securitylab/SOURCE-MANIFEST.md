# securitylab source manifest

This manifest records the final source state used for the archive import.

## Repository state

- Source repository: `techlittlebrawta/securitylab`
- Final default branch: `main`
- Final `main` commit: `a5a1187f1fbe184a6cf26030c0bf9fdbd5cb382f`
- Final `test` commit: `40030a1547194ff2322553164ba0e96f34f72156`
- Source tags: none
- Unique non-Ansible blobs on `test`: none
- Issues: none
- Releases: none
- GitHub Actions workflows: none
- Wiki pages: none; no Wiki Git repository existed

The following cleanup branch tips were also retained in destination Git history:

- `agent/remove-moved-empty-folders-main`: `70a47ca2ecd157e538cd35577a5c3a4e211ad6ce`
- `agent/remove-moved-empty-folders-test`: `dcd0f543ff1d0b0d30000964827557c655b9cbd9`
- `agent/remove-moved-vmware-main`: `00b1bf9b8a32ca288259b7c756cb679befaa8db1`
- `agent/remove-moved-vmware-test`: `b6d6b952ba672ff8e6908856e1c210aa62893f1e`

## Source pull-request record

The source repository had four pull requests, all created and merged during the
migration cleanup:

| PR | Base | Head | Merged (UTC) | Purpose |
| --- | --- | --- | --- | --- |
| 1 | `main` | `agent/remove-moved-empty-folders-main` | 2026-07-18 19:00:07 | Remove moved empty topic folders |
| 2 | `test` | `agent/remove-moved-empty-folders-test` | 2026-07-18 19:01:48 | Remove moved empty topic folders from test |
| 3 | `main` | `agent/remove-moved-vmware-main` | 2026-07-18 19:14:30 | Remove moved VMware lab files |
| 4 | `test` | `agent/remove-moved-vmware-test` | 2026-07-18 19:15:48 | Remove moved VMware placeholder from test |

## Preserved files

The Git blob IDs below must match the imported files. Repeated IDs represent
the original one-byte placeholder files.

| Original and archived path | Git blob ID |
| --- | --- |
| `README.md` | `f00b4c6eac7054557959db9873bd8f3128f71f7f` |
| `nmap/nmap_scan_subnet.yml` | `9e0d47665ac65abef052ba5db8de25c30ef9395e` |
| `pnetlab/README.md` | `8b137891791fe96927ad78e64b0aad7bded08bdc` |
| `pnetlab/pnetlab_add_nodes.py` | `00d900a6c277963ee9fa05534f57f54181d500b0` |
| `pnetlab/pnetlab_add_nodes_custom_payload.py` | `3db21c6dd5fc147d70ea1db314dcb97b9aa89a03` |
| `pnetlab/pnetlab_get_nodes_status.py` | `b123051f491c34dd042af1e67874cd00b822f483` |
| `pnetlab/pnetlab_main_script.py` | `42d53ea486769b9dc3003b7f0bf92bece4567cc6` |
| `pnetlab/pnetlab_start_all_nodes.py` | `cfc8881ff6cbf164e33290a528d17e1c5bb3e2b1` |
| `pnetlab/pnetlab_stop_all_nodes.py` | `b3e0f7933fb4705de46a250cb6fb6a82347adf94` |
| `pnetlab/pnetlab_wipe_all_nodes.py` | `d4261e1799a72b8dd7c4c5cc8b6c205ca9cd35bf` |
| `splunk/README.md` | `8b137891791fe96927ad78e64b0aad7bded08bdc` |
| `splunk/add-ons/README.md` | `8b137891791fe96927ad78e64b0aad7bded08bdc` |
| `splunk/add-ons/TA-veracode/bin/veracode.py` | `449909772f3ea4a6d6bb751f2fd68c18733eeb9a` |
| `splunk/add-ons/TA-veracode/data/README.md` | `8b137891791fe96927ad78e64b0aad7bded08bdc` |
| `splunk/add-ons/TA-veracode/local/inputs.conf` | `95c1fd52c9f38d5471ccf6afbb8ee2af149d5dc3` |
| `splunk/add-ons/TA-veracode/local/props.conf` | `6d1d8661e6eecebd522d905a58c427c675d36a40` |
| `splunk/add-ons/TA-veracode/metadata/default.meta` | `ec87c5a4a8d4cb5dfdfc9965ffcf0184d21eaca4` |
| `splunk/apps` | `8b137891791fe96927ad78e64b0aad7bded08bdc` |

## Excluded Ansible files

The four files beneath source `ansible/` were intentionally not retained in the
archive working tree because the destination's current Ansible implementation
supersedes them. Their history remains reachable through the imported source
history.
