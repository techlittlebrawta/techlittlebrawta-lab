# ESXi disposable-lab license recovery

> **Lab use only:** `vmware_esxi_license.yml` directly replaces an ESXi license
> configuration file and restarts `vpxa`. It is retained for recovery of a
> private, disposable lab host where rebuilding the host would otherwise be
> required. Do not run it in production or on a system you do not own and
> administer.

The playbook performs these original operations on every host in the `esxi`
inventory group:

1. Removes `/etc/vmware/license.cfg`.
2. Copies `/etc/vmware/.#license.cfg` to `/etc/vmware/license.cfg`.
3. Restarts the ESXi `vpxa` service.

These are direct, destructive host changes. If the hidden backup is missing,
invalid, or incompatible with the installed ESXi version, the host can be left
without a usable license configuration or management service.

## Requirements

- A private, disposable ESXi lab host that you are authorized to administer.
- An Ansible control machine that can reach the host over SSH.
- An inventory group named `esxi`.
- Administrative credentials with permission to change `/etc/vmware` and
  restart `vpxa`.
- A tested recovery path, such as a hypervisor snapshot, configuration backup,
  or installation media.

Example inventory structure:

```ini
[esxi]
lab-esxi.example.test ansible_host=192.0.2.50 ansible_user=root
```

Use Ansible Vault, an SSH agent, or another external secret mechanism. Do not
store the ESXi password or private key in this repository.

## Pre-run checks

Run these checks manually on the lab host before using the playbook:

```sh
ls -l /etc/vmware/license.cfg /etc/vmware/.#license.cfg
cp /etc/vmware/license.cfg /vmfs/volumes/DATASTORE/license.cfg.pre-lab-change
```

Replace `DATASTORE` with a datastore that will survive the host operation. Stop
if the hidden backup does not exist or if there is no separate recovery copy.

Preview the targeted hosts:

```sh
ansible-playbook -i inventory.ini vmware_esxi_license.yml --list-hosts
```

Run it only after confirming that every listed host is a disposable lab system:

```sh
ansible-playbook -i inventory.ini vmware_esxi_license.yml
```

## Recovery

If the host does not return to the expected state, restore the saved
`license.cfg`, restart the affected management services, revert the lab
snapshot, or reinstall the disposable ESXi host.

For normal licensing, use a valid license through the ESXi Host Client or
vSphere Client. Broadcom documents the supported assignment workflow in
[ESXi host remains in evaluation mode after license assignment](https://knowledge.broadcom.com/external/article/413268/esxi-host-remains-in-evaluation-mode-aft.html).

This repository does not grant a VMware license and does not override applicable
license terms.
