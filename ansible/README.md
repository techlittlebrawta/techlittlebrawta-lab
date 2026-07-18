# Install AAP 2.7 all-in-one on a fresh RHEL server

This folder contains a guided installer for a **new** Red Hat Enterprise Linux server. It installs the Red Hat Ansible Automation Platform (AAP) 2.7 **container growth topology**, sometimes called an all-in-one installation.

The finished server includes:

- Automation Gateway and the AAP web interface
- Automation Controller
- Private Automation Hub
- Event-Driven Ansible
- Automation Metrics
- PostgreSQL, Redis, and Receptor

You do not need to know Ansible or Podman to run the script. Read this page from top to bottom before starting.

## Important limitations

- Use this only on a fresh server that does not already run AAP.
- This creates a single-server lab deployment. It is not a highly available production design.
- The script installs AAP but does not provide a Red Hat subscription manifest or organization-specific TLS certificate.
- Keep the downloaded Red Hat installer bundle private. Do not upload it to GitHub.

## 1. Check the RHEL server

The server must have:

| Requirement | Minimum |
| --- | --- |
| Operating system | RHEL 9.6 or newer RHEL 9 release, or RHEL 10 |
| CPU | 4 virtual CPUs |
| Memory | 16 GiB; 20 GiB or more is recommended |
| Free local storage | 80 GiB available under `/home` |
| Architecture | `x86_64` or `aarch64` |
| Network | Access to enabled RHEL BaseOS and AppStream repositories |
| Account | Any account that can run `sudo` |

Connect to the server with SSH. Replace `YOUR_RHEL_USER` and `SERVER_IP` with real values:

```bash
ssh YOUR_RHEL_USER@SERVER_IP
```

Run these checks on the RHEL server:

```bash
cat /etc/redhat-release
uname -m
nproc
free -h
df -h /home
sudo subscription-manager status
sudo dnf repolist --enabled
```

Confirm that BaseOS and AppStream appear in the enabled repository list.

If the server is not registered, register it using the method provided by your Red Hat administrator. One interactive method is:

```bash
sudo subscription-manager register
```

Do not put Red Hat passwords or activation keys in this repository or in the installer script.

## 2. Get the Red Hat AAP installer bundle

Sign in to the [Red Hat Hybrid Cloud Console downloads page](https://console.redhat.com/ansible/automation-hub/repo/published/ansible-automation-platform-setup-bundle/distributions/) using an account entitled to AAP.

Download the AAP 2.7 **containerized setup bundle** that matches the server architecture. The filename resembles:

```text
ansible-automation-platform-containerized-setup-bundle-2.7-2-x86_64.tar.gz
```

Your release number might be newer than the example. Do not extract the bundle yourself.

## 3. Copy this `ansible` folder to the server

Choose one method.

### Method A: clone the repository on the RHEL server

Run on the RHEL server:

```bash
sudo dnf install -y git
git clone --depth 1 https://github.com/techlittlebrawta/techlittlebrawta-lab.git
cd techlittlebrawta-lab/ansible
```

### Method B: download without Git

Run on the RHEL server:

```bash
curl -L https://github.com/techlittlebrawta/techlittlebrawta-lab/archive/refs/heads/main.tar.gz -o /tmp/techlittlebrawta-lab.tar.gz
tar -xzf /tmp/techlittlebrawta-lab.tar.gz -C /tmp
cp -R /tmp/techlittlebrawta-lab-main/ansible "$HOME/ansible"
cd "$HOME/ansible"
```

### Method C: copy a folder from your workstation

First download or clone this repository on your Windows, macOS, or Linux workstation. Then run from a terminal on that workstation:

```bash
scp -r ansible YOUR_RHEL_USER@SERVER_IP:~/
```

Connect to the server and enter the folder:

```bash
ssh YOUR_RHEL_USER@SERVER_IP
cd ~/ansible
```

## 4. Put the Red Hat bundle beside the script

If the bundle is on your workstation, copy it to the server. Run this on the workstation, replacing every uppercase placeholder:

```bash
scp /PATH/TO/ansible-automation-platform-containerized-setup-bundle-2.7-*-x86_64.tar.gz \
  YOUR_RHEL_USER@SERVER_IP:~/ansible/
```

For an ARM server, the bundle filename will use its matching architecture instead of `x86_64`.

Back on the RHEL server, verify the folder:

```bash
cd ~/ansible
ls -lh
```

It should contain:

```text
README.md
install-aap-all-in-one.sh
ansible-automation-platform-containerized-setup-bundle-2.7-...tar.gz
```

## 5. Run the installer

Make the script executable and start it:

```bash
cd ~/ansible
chmod +x install-aap-all-in-one.sh
sudo ./install-aap-all-in-one.sh
```

The script shows a plan and asks for confirmation before making changes. It automatically detects the server's primary IPv4 address.

If the server has more than one network interface, specify the address that your workstation uses to reach it:

```bash
sudo ./install-aap-all-in-one.sh --ip SERVER_IP
```

You may also choose a friendly hostname. This does not require a DNS server because IP-based login remains available:

```bash
sudo ./install-aap-all-in-one.sh \
  --ip SERVER_IP \
  --fqdn aap01.lab.example.com
```

Use `--yes` only after reviewing the plan when running non-interactively:

```bash
sudo ./install-aap-all-in-one.sh --ip SERVER_IP --yes
```

Installation usually takes 30–60 minutes. Keep the terminal open. The complete log is stored at:

```text
/var/log/aap-all-in-one-install.log
```

## 6. Log in to AAP

When installation succeeds, the script prints:

- the IP address URL;
- an optional friendly hostname URL;
- the username `admin`;
- a randomly generated password.

The simplest login method is the server IP address:

```text
https://SERVER_IP
```

For example, if your server address is `10.20.30.40`, open:

```text
https://10.20.30.40
```

The generated certificate includes both the IP address and friendly hostname. Because the certificate authority is private to this installation, your browser will probably show a security warning the first time. Confirm that you are connecting to the expected server before accepting the warning.

Retrieve the login details later by running this on the RHEL server:

```bash
sudo cat /root/aap-login.txt
```

### Optional friendly hostname access

If there is no DNS server and you prefer the friendly URL, add the `Client hosts entry` shown in `/root/aap-login.txt` to the computer running the browser:

- Linux or macOS: `/etc/hosts`
- Windows: `C:\Windows\System32\drivers\etc\hosts`

This is optional. The IP address URL works without changing the browser computer's hosts file.

## 7. Check that AAP is running

AAP uses **rootless containers**. This means the containers belong to the dedicated `aap` Linux account, not to `root` and not to the account you used for SSH.

This command checks root's Podman storage and will normally show no AAP containers:

```bash
sudo podman ps
```

That empty result does **not** mean AAP is stopped.

Switch to the `aap` service account:

```bash
sudo -iu aap
```

Your command prompt changes because you are now operating as `aap`. List the AAP containers:

```bash
podman ps
```

You should see containers with names such as:

```text
automation-gateway
automation-gateway-proxy
automation-controller-web
automation-controller-task
automation-hub-api
automation-eda-api
automation-metrics-web
postgresql
redis-tcp
```

Check for stopped containers as well as running containers:

```bash
podman ps -a
```

List running AAP services:

```bash
systemctl --user --type=service --state=running
```

Check whether any AAP service failed:

```bash
systemctl --user --failed
```

A healthy system reports `0 loaded units listed` in the failed-unit output.

When finished, return to your normal SSH account:

```bash
exit
```

From your normal account, confirm that HTTPS is listening:

```bash
sudo ss -lntp | grep ':443'
```

Test the web interface. Replace `SERVER_IP` with the server's address:

```bash
curl -kI https://SERVER_IP
```

An HTTP response such as `200 OK` confirms that the web server answered. The `-k` option is needed because the initial AAP certificate is signed by the installation's private certificate authority.

To inspect one service in detail:

```bash
sudo -iu aap systemctl --user status automation-gateway-proxy.service
```

To display its latest log messages:

```bash
sudo -iu aap journalctl --user -u automation-gateway-proxy.service -n 100 --no-pager
```

The important distinction is:

```text
sudo podman ps          checks root's containers and usually appears empty
sudo -iu aap podman ps  checks the AAP rootless containers
```

## 8. Activate the AAP subscription

After logging in, follow the web interface prompt to attach an available Red Hat subscription or upload a subscription manifest. The exact choice depends on how your organization manages Red Hat subscriptions.

## What the script changes

The script:

1. Checks RHEL version, architecture, CPU, memory, local storage, registration, repositories, and bundle integrity.
2. Installs supported RHEL packages including Ansible Core and Podman.
3. Assigns a local AAP hostname and adds a matching entry to the server's `/etc/hosts` file.
4. Creates a dedicated `aap` service account with installer-required sudo access.
5. Extracts the bundle under `/home/aap` so container data uses the large `/home` filesystem.
6. Generates unique database and administrator passwords.
7. Opens the firewall ports configured by the supported Red Hat installer.
8. Runs the Red Hat AAP containerized installer.
9. Confirms that services are running and checks the HTTPS web interface using both the IP address and configured hostname.

## Troubleshooting

If the script stops, read the final error and inspect the log:

```bash
sudo less /var/log/aap-all-in-one-install.log
```

Check available storage:

```bash
df -h /home
```

Check the rootless AAP services:

```bash
sudo -iu aap
systemctl --user --failed
podman ps -a
exit
```

Check the web port:

```bash
sudo ss -lntp | grep ':443'
```

Do not repeatedly rerun the script after a partial installation without first understanding the failure. The script deliberately stops when it detects existing AAP data so that it does not replace previously generated database credentials.

## Protect these files

- `/root/aap-login.txt` contains the AAP administrator password.
- The generated inventory under `/home/aap/aap-install/` contains database passwords.
- Do not commit bundles, inventories, credentials, logs, certificates, or private keys to Git.
