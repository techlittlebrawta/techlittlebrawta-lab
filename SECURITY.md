# Security Policy

## Reporting a vulnerability

Do **not** disclose suspected vulnerabilities, credentials, tokens, private keys, or sensitive infrastructure details in a public issue.

For sensitive security reports, use GitHub's private vulnerability reporting/security advisory workflow for this repository when available, or contact the Tech Little Brawta repository owner privately through an approved organizational channel.

## Secrets

Never commit:
- passwords
- API keys or tokens
- private keys
- cloud credentials
- device credentials
- production configuration containing secrets
- license keys or vendor entitlement files

If a secret is committed, treat it as compromised and rotate/revoke it immediately.
