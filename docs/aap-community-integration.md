# AAP and Community Integration

AAP connects to `192.168.1.250` as `ansible`. The account can invoke only the
fixed root-owned maintenance interface through sudo. It cannot run an arbitrary
privileged shell.

Operator execution uses AAP's encrypted downstream credential. The job writes
one mode-0600 request and one mode-0600 secret envelope on the MBJ node. The
allowlisted runner deletes the secret before execution and deletes the request
on exit. Parameters are limited to a validated inventory expression and three
non-secret scalar fields.

The operational workflow performs health, Git sync, dependency validation,
inventory validation, direct endpoint connectivity, platform validation,
approved execution, and result verification. Success advances only on a zero
return code. The controlled-failure template proves a nonzero downstream result
is reported as an AAP failure.
