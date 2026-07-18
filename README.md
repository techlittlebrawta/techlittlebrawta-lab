# TechLittleBrawta Lab

Practical, reviewed lab automation and implementation notes for networking,
security, infrastructure, observability, and platform engineering.

Content migrated from the former
[`techlittlebrawta/securitylab`](https://github.com/techlittlebrawta/securitylab)
repository is recorded in [`MIGRATION.md`](MIGRATION.md). Code was reviewed and
either remediated or deliberately preserved according to the decisions recorded
there.

## Lab areas

| Area | Contents |
| --- | --- |
| [Ansible](ansible/) | AAP installation and legacy bundle examples |
| [Arista](arista/) | Arista networking documentation placeholder |
| [Aruba](aruba/) | Aruba networking documentation placeholder |
| [Cisco](cisco/) | Cisco networking documentation placeholder |
| [Extreme Networks](extremenetworks/) | Extreme Networks documentation placeholder |
| [Fortinet](fortinet/) | Fortinet security documentation placeholder |
| [Juniper](juniper/) | Juniper networking documentation placeholder |
| [Linux](linux/) | Linux administration documentation placeholder |
| [Microsoft](microsoft/) | Microsoft platform documentation placeholder |
| [Nmap](nmap/) | Authorized host-discovery automation |
| [Palo Alto Networks](paloalto/) | Palo Alto Networks documentation placeholder |
| [PNETLab](pnetlab/) | PNETLab installation and safer API tools |
| [Splunk](splunk/) | Splunk add-ons and application structure |
| [VMware](vmware/) | Clearly marked, disposable-lab-only ESXi automation |

## Safety and contribution rules

- Test automation in a disposable lab before using it in another environment.
- Review every README, variable, and destructive-operation warning first.
- Run security or discovery tools only on systems you own or are authorized to test.
- Use supported vendor APIs and documented administration workflows.
- Never commit passwords, tokens, API keys, license keys, private keys,
  certificates, production inventories, customer data, or proprietary images.
- Give each new project a README with requirements, configuration, usage,
  validation, rollback or recovery guidance, and known limitations.
- Add automated syntax checks or tests whenever practical.

Examples use reserved names such as `example.com` and placeholder addresses.
Replace them deliberately for the lab environment without putting secrets in
Git.
