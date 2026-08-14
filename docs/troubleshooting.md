# Troubleshooting

If AAP cannot reach MBJ, verify the Cloud0 attachment, `192.168.1.250/24`, route,
firewalld SSH service, and the `ansible` authorized key. If MBJ cannot reach a
node, verify `10.255.255.125/24`, the node's pnet9 interface and reservation,
and its declared management port.

For project failures, require a clean checkout and verify `git ls-remote origin
HEAD`. For TLS failures, verify the committed AAP public CA is installed and the
canonical controller name resolves to `192.168.1.251`; do not disable certificate
validation. For runner failures, correlate AAP job ID with the newest JSON
artifact and log, then use its host recap and Git SHA.

A stale request or secret indicates an interrupted pre-run task. Confirm no
runner is active, remove only the specifically identified stale UUID files, and
rerun the job. Never print their contents.
