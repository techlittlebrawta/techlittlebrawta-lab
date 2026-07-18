# AAP 2.7 all-in-one installer for RHEL

`install-aap-all-in-one.sh` prepares a fresh, registered RHEL host and installs the Red Hat Ansible Automation Platform 2.7 container growth topology. It deploys Gateway, Controller, Private Automation Hub, Event-Driven Ansible, Metrics, PostgreSQL, Redis, and Receptor as rootless Podman services.

## Requirements

- Fresh RHEL 9.6+ or RHEL 10 host
- Valid RHEL and AAP subscriptions
- 4 or more CPUs
- 16 GiB RAM minimum; 32 GiB is recommended for a bundled growth deployment
- At least 80 GiB available on the local `/home` filesystem
- Internet access to RHEL BaseOS and AppStream repositories
- One AAP 2.7 **containerized setup bundle** (`.tar.gz`)
- Root or sudo access

The script is for a new installation only. It refuses to run if it detects an existing AAP deployment.

## Copy the folder to the RHEL server

Clone the repository directly on the new RHEL server:

```bash
sudo dnf install -y git
git clone --depth 1 https://github.com/techlittlebrawta/techlittlebrawta-lab.git
cd techlittlebrawta-lab/ansible
```

Alternatively, copy only this folder from another workstation:

```bash
scp -r ansible root@192.168.1.251:/root/
ssh root@192.168.1.251
cd /root/ansible
```

Replace `192.168.1.251` with the address of the new RHEL server.

## Add the installer bundle

Download the AAP 2.7 containerized setup bundle from the Red Hat Customer Portal. Copy it into the same directory as the script:

```bash
scp ansible-automation-platform-containerized-setup-bundle-2.7-*-x86_64.tar.gz \
  root@192.168.1.251:/root/ansible/
```

The directory should resemble:

```text
ansible/
├── README.md
├── install-aap-all-in-one.sh
└── ansible-automation-platform-containerized-setup-bundle-2.7-2-x86_64.tar.gz
```

## Install

```bash
cd /root/ansible
chmod +x install-aap-all-in-one.sh
sudo ./install-aap-all-in-one.sh
```

The defaults automatically select the first non-loopback IPv4 address and use a DNS-less lab hostname such as `aap.servername.lab.example.com`. Override them when needed:

```bash
sudo ./install-aap-all-in-one.sh \
  --fqdn aap01.lab.example.com \
  --ip 192.168.1.251
```

For unattended execution after reviewing the script and parameters:

```bash
sudo ./install-aap-all-in-one.sh \
  --fqdn aap01.lab.example.com \
  --ip 192.168.1.251 \
  --yes
```

The installation commonly takes 30–60 minutes. Progress is written to:

```text
/var/log/aap-all-in-one-install.log
```

## Log in

After successful installation, the script prints the URL and generated admin password. A root-readable copy is stored at:

```text
/root/aap-login.txt
```

For a lab without DNS, add the `Client hosts entry` from that file to the workstation used to browse AAP:

- Linux/macOS: `/etc/hosts`
- Windows: `C:\Windows\System32\drivers\etc\hosts`

Then open the displayed HTTPS URL and log in as `admin`. The installer generates a private certificate authority, so the browser may initially show a certificate trust warning.

## Security and operational notes

- Generated inventory and credential files are mode `0600`.
- The dedicated `aap` account receives passwordless sudo because the supported containerized installer needs privilege escalation.
- Do not commit the Red Hat installer bundle, generated inventory, passwords, logs, or certificates to Git.
- Attach the AAP subscription or manifest in the web interface after installation if it was not supplied during deployment.
