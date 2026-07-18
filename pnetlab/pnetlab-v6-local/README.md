# PNETLab 6 and iShare2 installer

This directory contains a zero-touch installer for PNETLab 6.0.0-103 and
iShare2 on a fresh Ubuntu 20.04 AMD64 server.

The installer:

- validates Ubuntu, architecture, Secure Boot state, and all local archives;
- installs Ubuntu, PHP 7.4, MySQL, Docker, virtualization, and console dependencies;
- configures the MySQL authentication required by the PNETLab packages;
- installs the PNETLab kernel and all PNETLab 6.0.0-103 components;
- replaces `systemd-timesyncd` atomically with PNETLab's required `ntp` service;
- downloads iShare2 from its official `main` branch and selects its defaults;
- verifies packages, services, database state, web access, and iShare2; and
- schedules the required reboot into the PNETLab kernel.

## Requirements

- Fresh Ubuntu Server 20.04 on AMD64/x86-64
- Root or `sudo` access
- Internet access for Ubuntu dependencies and iShare2
- Hardware virtualization or nested virtualization
- UEFI Secure Boot disabled
- The eleven authorized local PNETLab files listed in [`packages/PLACE_FILES_HERE.txt`](packages/PLACE_FILES_HERE.txt)

The package archives are intentionally excluded from Git because several
exceed GitHub's normal per-file size limit. Obtain the PNETLab packages from an
authorized source and retain the exact filenames.

## Directory layout

```text
pnetlab/
├── install_pnetlab_v6_and_ishare2.sh
└── packages/
    └── [the eleven required ZIP and DEB files]
```

## Install

Transfer the complete directory to the Ubuntu server, then run:

```bash
cd pnetlab
chmod 700 install_pnetlab_v6_and_ishare2.sh
sudo ./install_pnetlab_v6_and_ishare2.sh
```

The installation is noninteractive. When successful, the server schedules a
reboot after one minute. The log is stored at:

```text
/var/log/pnetlab-ishare2-install.log
```

The upstream initial PNETLab credentials are `root` / `pnet`. Change the root
password immediately after installation and restrict root SSH access before
connecting the server to an untrusted network.

To prevent the automatic reboot when another automation will handle it:

```bash
sudo PNETLAB_AUTO_REBOOT=0 ./install_pnetlab_v6_and_ishare2.sh
```

To use a package directory stored elsewhere:

```bash
sudo PNETLAB_PACKAGE_DIR=/absolute/path/to/packages ./install_pnetlab_v6_and_ishare2.sh
```
