# Legacy AAP 2.4 bundle installation examples

This directory preserves and corrects the standalone Automation Controller and
Private Automation Hub inventory examples migrated from
`techlittlebrawta/securitylab`.

AAP 2.4 is an older release. For a new lab, prefer the current containerized AAP
installer documented in the parent [`ansible/`](../../) directory. Use these
examples only when an existing AAP 2.4 entitlement or compatibility requirement
specifically calls for the 2.4 setup bundle.

## Corrections made during migration

- Renamed plain text inventory files to `.example.ini`.
- Corrected inventory group names to lowercase `[automationcontroller]` and
  `[automationhub]` as required by the installer.
- Replaced lab-specific hostnames with safe example FQDNs.
- Removed registry credentials from the bundle example because Red Hat requires
  them for the online installer, not the disconnected setup bundle.
- Uses the documented `awx` controller database name and user.
- Documents root execution, inventory protection, validation, and web login.
- Adds ignore rules for bundles, real inventories, logs, certificates, and keys.

## Before starting

You need:

- a Red Hat account and active AAP 2.4 entitlement;
- a supported, registered RHEL system with the required repositories;
- the AAP 2.4 setup bundle downloaded from Red Hat;
- working forward and reverse DNS for each node; and
- root or `sudo` access.

Do not use `localhost` as an inventory hostname. Use a reachable FQDN. For a
production or customer environment, do not place Automation Controller and
Private Automation Hub on the same node; Red Hat documents them as separate
services because co-location can cause resource contention.

Review the official version-specific guide before installation:
[Red Hat AAP 2.4 installation guide](https://docs.redhat.com/en/documentation/red_hat_ansible_automation_platform/2.4/html/red_hat_ansible_automation_platform_installation_guide/index).

## Standalone Automation Controller

1. Copy `inventory-controller.example.ini` to the extracted setup bundle as
   `inventory`.
2. Replace `controller.example.com` with the controller's reachable FQDN.
3. Replace every `CHANGE_ME` password.

## Standalone Private Automation Hub

1. Copy `inventory-hub.example.ini` to the extracted setup bundle as `inventory`.
2. Replace `hub.example.com` with the hub's reachable FQDN.
3. Replace every `CHANGE_ME` password.

The empty `[automationcontroller]` group in the hub-only example is deliberate.

## Protect and validate the inventory

The inventory contains administrator and database passwords and is needed for
future backup, restore, and upgrade operations:

```bash
chmod 600 inventory
grep -n CHANGE_ME inventory
ansible all -i inventory --list-hosts
```

The `grep` command must return no lines after all placeholders are replaced.
Store an encrypted backup of the completed inventory outside this repository.

## Install

From the extracted AAP 2.4 setup-bundle directory:

```bash
sudo -i
cd /path/to/ansible-automation-platform-setup-bundle-2.4-*
./setup.sh
```

When the installer completes, open the configured FQDN in a browser and sign in
as `admin` with the inventory's administrator password. Confirm that the
selected Controller or Hub service loads and that no installer play failed.

Do not commit the setup bundle or completed inventory.
