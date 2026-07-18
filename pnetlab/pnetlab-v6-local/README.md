# PNETLab 6 and iShare2 zero-touch installer

This directory contains a noninteractive installer for PNETLab 6.0.0-103 and
iShare2 on a fresh Ubuntu 20.04.6 AMD64/x86-64 computer or virtual machine.

Read and complete the preparation sections below before running the script.
After preparation, the script installs the prerequisites, PNETLab, and iShare2,
accepts the iShare2 defaults, validates the installation, and schedules the
required reboot without asking the user questions.

## What the installer does

- confirms that the operating system is Ubuntu 20.04 and the architecture is AMD64;
- confirms that all eleven required PNETLab files exist and are valid archives;
- installs the Ubuntu, PHP 7.4, MySQL, Docker, virtualization, and console prerequisites;
- configures the MySQL authentication required by the PNETLab packages;
- installs the PNETLab 6.0.0-103 packages and custom kernel;
- replaces `systemd-timesyncd` with PNETLab's required `ntp` service;
- downloads the current official iShare2 script and accepts all iShare2 defaults;
- verifies the packages, services, database, web interface, and iShare2; and
- reboots the system into the PNETLab kernel one minute after a successful installation.

## 1. Download Ubuntu 20.04.6

Download the official 64-bit Ubuntu 20.04.6 Desktop ISO:

- [ubuntu-20.04.6-desktop-amd64.iso](https://releases.ubuntu.com/focal/ubuntu-20.04.6-desktop-amd64.iso)
- [Ubuntu 20.04.6 release page and SHA256 checksums](https://releases.ubuntu.com/focal/)

Use Ubuntu **20.04.6 AMD64**. The installer intentionally stops on Ubuntu
22.04, 24.04, ARM64, or any other operating-system version because the included
PNETLab packages were built for Ubuntu 20.04 AMD64.

On Windows, the downloaded ISO can be checked in PowerShell with:

```powershell
Get-FileHash "$env:USERPROFILE\Downloads\ubuntu-20.04.6-desktop-amd64.iso" -Algorithm SHA256
```

Compare the displayed hash with the `ubuntu-20.04.6-desktop-amd64.iso` entry in
the `SHA256SUMS` file on the Ubuntu release page before using the ISO.

## 2. Allocate enough hardware

For a small lab, start with at least:

- 4 virtual CPUs;
- 8 GB RAM;
- 40 GB disk space; and
- one network adapter with Internet access and an IP address reachable from your computer.

For a more useful general-purpose lab, use approximately:

- 8 virtual CPUs;
- 24 GB RAM; and
- 200 GB disk space.

Larger or more numerous virtual routers and firewalls require more CPU, memory,
and storage. These starting points follow PNETLab's published minimum and
recommended virtual-machine requirements. Storage can usually be expanded
later, but it is difficult to shrink.

## 3. Understand the virtualization requirement

PNETLab runs other virtual machines inside itself. Therefore, seeing the PNETLab
web page is not enough: Intel VT-x/EPT or AMD-V/RVI must be available inside the
Ubuntu system or hardware-accelerated QEMU nodes will not start.

### If Ubuntu is installed directly on a physical computer

Enter the physical computer's BIOS/UEFI setup before installing Ubuntu and
enable the applicable CPU virtualization option. Manufacturers use names such as:

- **Intel Virtualization Technology**, **Intel VT-x**, or **VMX**; or
- **SVM Mode**, **AMD-V**, or **Secure Virtual Machine**.

Save the firmware settings and fully power-cycle the computer. Secure Boot must
also be disabled in the physical computer's UEFI settings because PNETLab uses
an unsigned custom kernel.

### If Ubuntu is an ESXi virtual machine

Nested virtualization must be enabled for the PNETLab VM. The physical ESXi
host must first support Intel VT-x/EPT or AMD-V/RVI and have virtualization
enabled in the host's BIOS/UEFI.

With the PNETLab VM completely powered off:

1. In the vSphere Client, select the PNETLab VM.
2. Right-click the VM and select **Edit Settings**.
3. Open the **Virtual Hardware** tab.
4. Expand **CPU**.
5. Under **Hardware virtualization**, check
   **Expose hardware-assisted virtualization to the guest OS**.
6. Click **OK**.

A guest restart is not the same as powering off the VM. If the option cannot be
selected, power off the VM and confirm that virtualization is enabled in the
physical ESXi host's BIOS/UEFI. A VM using vGPU or PCI/DirectPath I/O may be
unable to use ESXi nested virtualization; remove that passthrough device or use
a separate VM.

After Ubuntu is installed, verify that virtualization is visible inside the VM:

```bash
grep -Eom1 'vmx|svm' /proc/cpuinfo
```

The command must print `vmx` for Intel or `svm` for AMD. No output means the
virtualization feature is not being passed through. Correct the hypervisor or
physical BIOS/UEFI settings before installing PNETLab.

## 4. Configure ESXi EFI and Secure Boot correctly

For this PNETLab VM, use EFI firmware but **do not enable UEFI Secure Boot**.
The required settings are:

- **Firmware:** `EFI`
- **Enable UEFI Secure Boot:** unchecked/off
- **Virtualization Based Security:** unchecked/off, if that option is present

With the VM completely powered off:

1. In the vSphere Client, right-click the PNETLab VM and select **Edit Settings**.
2. Open the **VM Options** tab.
3. Expand **Boot Options**.
4. Set **Firmware** to **EFI**.
5. Uncheck **Enable UEFI Secure Boot**.
6. Click **OK**.

This setting applies to the PNETLab guest VM. It does not require disabling
Secure Boot on the ESXi host itself. If installing directly on physical
hardware, disable Secure Boot in that physical machine's UEFI instead.

The installer checks the guest's Secure Boot state and stops before installing
the unsigned PNETLab kernel if Secure Boot is still enabled.

## 5. Create and install the Ubuntu VM on ESXi

1. Create a new virtual machine in ESXi/vSphere.
2. Select a Linux/Ubuntu 64-bit guest type.
3. Allocate the CPU, RAM, disk, and network adapter described above.
4. Connect the network adapter to a port group that provides Internet access
   and is reachable from the computer that will manage PNETLab.
5. Add or edit the virtual CD/DVD drive, select the Ubuntu ISO, and check
   **Connect at power on**.
6. Apply the nested-virtualization and Secure Boot settings from sections 3 and 4.
7. Power on the VM and open its console.
8. Select **Install Ubuntu**.
9. Follow the Ubuntu installer, select the virtual disk when asked where to
   install, choose the timezone, and create a normal user and password.
10. Restart when Ubuntu requests it, disconnect the ISO if necessary, and sign
    in with the user created during installation.

Either Ubuntu's normal or minimal desktop installation is acceptable. Do not
install a newer Ubuntu release when prompted.

Open Terminal in Ubuntu and confirm that the machine has an IP address and DNS:

```bash
ip -br address
getent hosts archive.ubuntu.com
```

The first command should show an IPv4 address on the connected network
interface. The second should return one or more addresses. Fix the VM's network
or DNS before continuing if either check fails. A DHCP reservation or static IP
is recommended so the PNETLab web address does not change later.

### Optional ESXi port-group settings for external lab networks

No port-group security change is needed merely to install PNETLab or open its
management web page. However, lab routers, firewalls, and containers use MAC
addresses different from the PNETLab VM's own virtual NIC. If those nested
devices must connect through a PNETLab **Cloud** network to the physical LAN,
ESXi's default security policy can block their traffic.

Use a dedicated lab port group rather than weakening a production management
port group. For a vSphere Standard Switch port group, open the port group's
**Security** settings and set these to **Accept**:

- **Promiscuous mode**;
- **MAC address changes**; and
- **Forged transmits**.

For a vSphere Distributed Switch, MAC Learning is preferred where available;
enable MAC Learning and allow MAC address changes and forged transmits. VLAN
trunks also require the intended VLAN range on the distributed port group and
on the upstream physical switch.

These settings permit additional MAC addresses and reduce network isolation.
Apply them only to a dedicated, trusted lab network. Leave the management port
group at its normal security defaults unless the lab design specifically needs
nested devices bridged onto that network.

## 6. Download the installer bundle and PNETLab packages

### Download the GitHub files

From Ubuntu's web browser:

1. Open the [techlittlebrawta-lab repository](https://github.com/techlittlebrawta/techlittlebrawta-lab).
2. Select **Code**, then **Download ZIP**.
3. Open Ubuntu's **Files** application, go to **Downloads**, right-click the ZIP,
   and select **Extract Here**.
4. Open the extracted repository and browse to
   `pnetlab/pnetlab-v6-local`.

The installer script is named `install_pnetlab_v6_and_ishare2.sh`.

### Download the eleven PNETLab files

The package archives are excluded from GitHub because several exceed GitHub's
normal per-file size limit. Download all required files from:

- [LabHub PNETLab focal package directory](https://drive.labhub.eu.org/0:/pnetlab/upgrades_pnetlab/focal/)

Place the following eleven files inside the extracted
`pnetlab/pnetlab-v6-local/packages/` directory:

```text
pnetlab_kernel.zip
pre-docker.zip
swtpm-focal.zip
pnetlab-guacamole_6.0.0-7_amd64.deb
pnetlab-dynamips_6.0.0-30_amd64.deb
pnetlab-schema_6.0.0-30_amd64.deb
pnetlab-vpcs_6.0.0-30_amd64.deb
pnetlab-qemu_6.0.0-30_amd64.deb
pnetlab-docker_6.0.0-30_amd64.deb
pnetlab_6.0.0-103_amd64.deb
pnetlab-wireshark_6.0.0-30_amd64.deb
```

Do not extract the three ZIP files. Do not rename any file. If the browser adds
text such as `(1)` to a duplicate filename, remove that added text. The installer
stops before changing the system if a required file is missing, empty, corrupt,
or incorrectly named.

The completed directory must look like this:

```text
pnetlab-v6-local/
├── README.md
├── install_pnetlab_v6_and_ishare2.sh
└── packages/
    ├── pnetlab_kernel.zip
    ├── pre-docker.zip
    ├── swtpm-focal.zip
    ├── pnetlab-guacamole_6.0.0-7_amd64.deb
    ├── pnetlab-dynamips_6.0.0-30_amd64.deb
    ├── pnetlab-schema_6.0.0-30_amd64.deb
    ├── pnetlab-vpcs_6.0.0-30_amd64.deb
    ├── pnetlab-qemu_6.0.0-30_amd64.deb
    ├── pnetlab-docker_6.0.0-30_amd64.deb
    ├── pnetlab_6.0.0-103_amd64.deb
    └── pnetlab-wireshark_6.0.0-30_amd64.deb
```

The same checklist is available in
[`packages/PLACE_FILES_HERE.txt`](packages/PLACE_FILES_HERE.txt).

## 7. Run the installer

In Ubuntu's **Files** application, open the `pnetlab-v6-local` directory,
right-click an empty area, and select **Open in Terminal**. Then run:

```bash
chmod 700 install_pnetlab_v6_and_ishare2.sh
sudo ./install_pnetlab_v6_and_ishare2.sh
```

Enter the Ubuntu user's password when `sudo` requests it. This is the only
expected prompt. Do not close the terminal, press `Ctrl+C`, shut down the VM, or
start another package installation while the script is running.

The process can take 15 minutes to more than an hour depending on Internet,
storage, and CPU speed. The script selects all iShare2 defaults automatically.
After a successful installation it displays a success message and schedules a
reboot in one minute. Allow that reboot to occur.

The complete installation log is stored at:

```text
/var/log/pnetlab-ishare2-install.log
```

## 8. Complete first access after the reboot

Wait for Ubuntu and the PNETLab services to start, then determine the management
IP address from the VM console or by running:

```bash
hostname -I
```

From another computer on the same reachable network, open:

```text
https://PNETLAB-IP-ADDRESS/
```

If HTTPS does not answer, try `http://PNETLAB-IP-ADDRESS/`. A browser may warn
about the initial self-signed HTTPS certificate; confirm that the address is the
PNETLab VM before continuing.

PNETLab's first-time setup credentials are:

```text
Username: root
Password: pnet
```

Complete the initial PNETLab setup. Keep the displayed defaults if no custom
network settings are required. After choosing **Offline Mode**, the default web
account is:

```text
Username: admin
Password: pnet
```

Online Mode instead requires registering or signing in with a PNETLab online
account. Change all default passwords immediately, especially before exposing
the system beyond a trusted management network.

Confirm iShare2 is installed with:

```bash
sudo ishare2 --version
```

## Troubleshooting

### The installer reports that virtualization is not exposed

Power off the PNETLab VM. In ESXi, return to **Edit Settings** >
**Virtual Hardware** > **CPU** and check
**Expose hardware-assisted virtualization to the guest OS**. Then power on the
VM and confirm that this prints `vmx` or `svm`:

```bash
grep -Eom1 'vmx|svm' /proc/cpuinfo
```

### The installer reports that Secure Boot is enabled

Power off the VM. In ESXi, return to **Edit Settings** > **VM Options** >
**Boot Options**, keep firmware set to **EFI**, and uncheck
**Enable UEFI Secure Boot**. Power on the VM and run the installer again.

### A required package is missing or corrupt

Compare the `packages/` directory with the eleven exact filenames in section 6.
Re-download the named file, do not extract ZIP archives, and run the installer
again.

### An installation step fails

Read the final error on screen and inspect the last 100 log lines:

```bash
sudo tail -n 100 /var/log/pnetlab-ishare2-install.log
```

Correct the reported problem, then rerun the same installer command. An APT
`exit 100` error commonly indicates a repository, DNS, Internet, package-state,
or dependency problem; the lines immediately before the final error identify
the actual cause.

## Optional installer controls

To prevent the automatic reboot when another automation will handle it:

```bash
sudo PNETLAB_AUTO_REBOOT=0 ./install_pnetlab_v6_and_ishare2.sh
```

A reboot into kernel `5.17.15-pnetlab-uksm-2` is still required.

To use a package directory stored elsewhere:

```bash
sudo PNETLAB_PACKAGE_DIR=/absolute/path/to/packages ./install_pnetlab_v6_and_ishare2.sh
```

## Reference documentation

- [PNETLab hardware requirements](https://www.pnetlab.com/pages/documentation?slug=hardware-requirements)
- [PNETLab installation and first login](https://pnetlab.com/pages/download)
- [PNETLab online and offline modes](https://pnetlab.com/pages/documentation?slug=system-mode-in-pnetlab)
- [PNETLab: ESXi Cloud Management network troubleshooting](https://pnetlab.com/pages/documentation?slug=can-not-get-ip-from-cloud-management-on-esxi)
- [Broadcom: enable or disable UEFI Secure Boot for an ESXi VM](https://knowledge.broadcom.com/external/article/377377/enable-or-disable-uefi-secure-boot-for-a.html)
- [Broadcom: expose hardware-assisted virtualization to an ESXi guest](https://knowledge.broadcom.com/external/article/423240/an-event-occurs-on-the-windows-guest-os.html)
- [Broadcom: security implications of permissive vSphere port-group policies](https://knowledge.broadcom.com/external/article/446719/security-implications-of-enabling-promis.html)
