# Nmap automation

This folder contains an Ansible playbook that installs Nmap on an authorized
scanner host and performs host discovery (`nmap -sn`) against one approved
address, hostname, or CIDR.

Only scan systems and networks that you own or are explicitly authorized to
test. Host discovery can trigger monitoring and security controls.

## Improvements over the migrated playbook

- Replaces the hard-coded controller hostname with an inventory group.
- Replaces the hard-coded subnet with the `nmap_target` variable.
- Uses `ansible.builtin.package` instead of assuming YUM.
- Uses `ansible.builtin.command` with an argument list instead of a shell.
- Rejects command options, whitespace, and shell metacharacters in the target.
- Marks discovery as read-only so Ansible does not report a false change.

## Prepare inventory

Copy the example and replace the host and SSH user:

```bash
cp inventory.example.ini inventory.ini
chmod 600 inventory.ini
```

Do not commit a real inventory if it exposes internal hostnames, addresses, SSH
keys, or credentials.

Verify access:

```bash
ansible -i inventory.ini nmap_scanners -m ansible.builtin.ping
```

## Run

The default target is `192.168.1.0/24`. Override it explicitly for the approved
network:

```bash
ansible-playbook -i inventory.ini scan-subnet.yml \
  -e nmap_target=10.20.30.0/24
```

The playbook installs Nmap if needed and prints Nmap's host-discovery output. It
does not perform a port scan.

## Validate

Before use, run:

```bash
ansible-playbook -i inventory.example.ini scan-subnet.yml --syntax-check
```
