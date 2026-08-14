# Credentials and Secrets

No private key, password, token, vault material, or private certificate belongs
in this repository. The committed AAP certificate is public CA material only.

AAP stores the MBJ SSH private key and the encrypted downstream lab credential.
The latter is injected only into approved jobs as `TLB_LAB_PASSWORD`. AAP's
credential-migration job transfers the existing encrypted lab value to the new
custom credential without printing it or storing it in the project checkout.

On MBJ, transient request and secret directories are mode 0700. Envelopes are
mode 0600, consumed once, and removed on success or failure. Logs and JSON
artifacts are redacted. Rotate credentials in AAP, validate a read-only job,
then invalidate the previous value. Rotate the SSH key by adding the new public
key, updating AAP, validating, and removing the old public key.
