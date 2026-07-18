# Original Nmap playbook usage

[`nmap_scan_subnet.yml`](nmap_scan_subnet.yml) is preserved byte-for-byte from
the former `securitylab` repository.

## Purpose and fixed assumptions

The playbook:

1. Targets an Ansible host named `LAB-AAP-CONT-01`.
2. Uses privilege escalation.
3. Installs `nmap` with the `yum` module.
4. runs `nmap -sn 192.168.1.0/24` through a shell task.
5. Prints the raw output and output lines.

It does not accept the target host or subnet as variables. Run it unchanged only
when those exact values describe an authorized lab. For another environment,
copy the playbook outside this archive and edit the working copy.

## Requirements

- Ansible on the control node.
- An inventory entry matching `LAB-AAP-CONT-01`.
- Privilege-escalation permission on that managed host.
- A Red Hat-family managed host with a working `yum` configuration.
- Written authorization to scan `192.168.1.0/24`.

Example command:

```sh
ansible-playbook -i inventory.ini nmap_scan_subnet.yml --ask-become-pass
```

## Risks and limitations

- Never scan a network without permission.
- The package-install task changes the managed host.
- The scan uses a hard-coded private subnet and shell execution.
- The task does not set `changed_when`, so scan reporting may appear changed.
- There is no automated test or result parser.

## Validation and recovery

Preview the selected host before running:

```sh
ansible-playbook -i inventory.ini nmap_scan_subnet.yml --list-hosts
```

The discovery scan itself does not configure discovered devices. The only
persistent playbook change is installing `nmap`; remove that package manually if
the lab host should be returned to its earlier state.
