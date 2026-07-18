#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly AAP_USER="${AAP_USER:-aap}"
readonly AAP_HOME="/home/${AAP_USER}"
readonly STAGE_DIR="${AAP_HOME}/aap-install"
readonly LOGIN_FILE="/root/aap-login.txt"
readonly LOG_FILE="/var/log/aap-all-in-one-install.log"

FQDN="${AAP_FQDN:-}"
HOST_IP="${AAP_IP:-}"
BUNDLE="${AAP_BUNDLE:-}"
ASSUME_YES=false

usage() {
  cat <<'EOF'
Usage: sudo ./install-aap-all-in-one.sh [options]

Options:
  --fqdn NAME     FQDN for AAP (default: aap.<current-shortname>.lab.example.com)
  --ip ADDRESS    Server IPv4 address (default: first non-loopback IPv4 address)
  --bundle PATH   AAP 2.7 containerized setup bundle (default: single *.tar.gz beside script)
  --yes           Skip the confirmation prompt
  -h, --help      Show this help

Environment equivalents: AAP_FQDN, AAP_IP, AAP_BUNDLE, AAP_USER.
EOF
}

log() { printf '[%(%F %T)T] %s\n' -1 "$*" | tee -a "$LOG_FILE"; }
die() { log "ERROR: $*"; exit 1; }

while (($#)); do
  case "$1" in
    --fqdn) FQDN="${2:?Missing value for --fqdn}"; shift 2 ;;
    --ip) HOST_IP="${2:?Missing value for --ip}"; shift 2 ;;
    --bundle) BUNDLE="${2:?Missing value for --bundle}"; shift 2 ;;
    --yes) ASSUME_YES=true; shift ;;
    -h|--help) usage; exit 0 ;;
    *) usage >&2; die "Unknown option: $1" ;;
  esac
done

[[ $EUID -eq 0 ]] || die "Run this script as root or with sudo."
touch "$LOG_FILE"
chmod 0600 "$LOG_FILE"
exec > >(tee -a "$LOG_FILE") 2>&1
trap 'rc=$?; log "Installation stopped with exit code ${rc}. Review ${LOG_FILE}."; exit "$rc"' ERR

source /etc/os-release
[[ ${ID:-} == rhel ]] || die "This installer supports Red Hat Enterprise Linux only."
RHEL_MAJOR="${VERSION_ID%%.*}"
case "$RHEL_MAJOR" in
  9) (( ${VERSION_ID#*.} >= 6 )) || die "AAP 2.7 requires RHEL 9.6 or later." ;;
  10) ;;
  *) die "AAP 2.7 requires RHEL 9.6+ or RHEL 10." ;;
esac
case "$(uname -m)" in x86_64|aarch64) ;; *) die "Unsupported architecture: $(uname -m)" ;; esac

if [[ -z $BUNDLE ]]; then
  mapfile -t bundles < <(find "$SCRIPT_DIR" -maxdepth 1 -type f \
    -name 'ansible-automation-platform-containerized-setup-bundle-2.7-*.tar.gz' -print)
  ((${#bundles[@]} == 1)) || die "Place exactly one AAP 2.7 containerized setup bundle beside this script, or use --bundle."
  BUNDLE="${bundles[0]}"
fi
[[ -r $BUNDLE ]] || die "Cannot read bundle: $BUNDLE"
tar -tzf "$BUNDLE" >/dev/null || die "Bundle archive validation failed."

short_name="$(hostname -s | tr '[:upper:]' '[:lower:]')"
[[ -n $FQDN ]] || FQDN="aap.${short_name}.lab.example.com"
[[ $FQDN == *.* && $FQDN != *[A-Z]* ]] || die "FQDN must be lowercase and contain a domain: $FQDN"
if [[ -z $HOST_IP ]]; then
  HOST_IP="$(ip -4 -o addr show scope global | awk 'NR==1 {split($4,a,"/"); print a[1]}')"
fi
[[ $HOST_IP =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]] || die "Unable to determine a valid IPv4 address. Use --ip."

available_home_gib="$(df -BG --output=avail "$AAP_HOME" 2>/dev/null | awk 'NR==2 {gsub(/G/,""); print $1}')"
if [[ -z $available_home_gib ]]; then
  available_home_gib="$(df -BG --output=avail /home | awk 'NR==2 {gsub(/G/,""); print $1}')"
fi
(( available_home_gib >= 80 )) || die "/home needs at least 80 GiB available; found ${available_home_gib} GiB."
(( $(nproc) >= 4 )) || die "At least 4 CPUs are required."
mem_gib="$(( $(awk '/MemTotal/ {print $2}' /proc/meminfo) / 1024 / 1024 ))"
(( mem_gib >= 16 )) || die "At least 16 GiB RAM is required."

if [[ -d ${AAP_HOME}/aap || -e ${AAP_HOME}/.config/systemd/user/automation-gateway.service ]]; then
  die "An existing AAP deployment was detected. This script is for fresh installations only."
fi

cat <<EOF
AAP 2.7 growth all-in-one installation plan
  RHEL:       ${PRETTY_NAME}
  Hostname:   ${FQDN}
  IPv4:       ${HOST_IP}
  Service user: ${AAP_USER}
  Bundle:     ${BUNDLE}
  Storage:    ${available_home_gib} GiB available on /home
  Components: Gateway, Controller, Hub, EDA, Metrics, PostgreSQL, Redis
EOF
if ! $ASSUME_YES; then
  read -r -p 'Continue? [y/N] ' answer
  [[ $answer =~ ^[Yy]$ ]] || exit 0
fi

log "Validating Red Hat registration and repositories"
subscription-manager identity >/dev/null || die "Register this host with Red Hat before continuing."
subscription-manager status | grep -q 'Overall Status: Registered' || die "Red Hat registration is not active."
repo_list="$(dnf -q repolist --enabled)"
grep -qi baseos <<<"$repo_list" || die "Enable the RHEL BaseOS repository."
grep -qi appstream <<<"$repo_list" || die "Enable the RHEL AppStream repository."

log "Installing host prerequisites"
dnf install -y ansible-core podman sudo tar gzip openssl curl firewalld python3-firewall
ansible_version="$(ansible --version | awk 'NR==1 {gsub(/[][]/,"",$3); print $3}')"
case "$RHEL_MAJOR" in
  9) [[ $ansible_version == 2.14.* ]] || die "RHEL 9 requires ansible-core 2.14; installed ${ansible_version}." ;;
  10) [[ $ansible_version == 2.16.* ]] || die "RHEL 10 requires ansible-core 2.16; installed ${ansible_version}." ;;
esac

log "Configuring hostname and local resolution"
hostnamectl set-hostname "$FQDN"
sed -i '/^# BEGIN AAP LAB$/,/^# END AAP LAB$/d' /etc/hosts
cat >>/etc/hosts <<EOF
# BEGIN AAP LAB
${HOST_IP} ${FQDN} ${FQDN%%.*}
# END AAP LAB
EOF
getent ahostsv4 "$FQDN" | grep -q "^${HOST_IP}[[:space:]]" || die "Local FQDN resolution validation failed."

log "Creating dedicated rootless AAP service account"
id "$AAP_USER" &>/dev/null || useradd --create-home --home-dir "$AAP_HOME" --shell /bin/bash "$AAP_USER"
cat >"/etc/sudoers.d/${AAP_USER}" <<EOF
${AAP_USER} ALL=(ALL) NOPASSWD: ALL
EOF
chmod 0440 "/etc/sudoers.d/${AAP_USER}"
visudo -cf "/etc/sudoers.d/${AAP_USER}"
loginctl enable-linger "$AAP_USER"
user_uid="$(id -u "$AAP_USER")"
systemctl start "user@${user_uid}.service"

log "Staging the offline installer on /home"
install -d -o "$AAP_USER" -g "$AAP_USER" -m 0750 "$STAGE_DIR"
tar -xzf "$BUNDLE" -C "$STAGE_DIR"
installer_dir="$(find "$STAGE_DIR" -mindepth 1 -maxdepth 1 -type d -name 'ansible-automation-platform-containerized-setup-bundle-2.7-*' -print -quit)"
[[ -n $installer_dir ]] || die "Could not locate the extracted installer directory."
chown -R "$AAP_USER:$AAP_USER" "$STAGE_DIR"

secret() { openssl rand -hex 24; }
postgres_password="$(secret)"
gateway_admin_password="$(secret)"
gateway_pg_password="$(secret)"
controller_admin_password="$(secret)"
controller_pg_password="$(secret)"
hub_admin_password="$(secret)"
hub_pg_password="$(secret)"
eda_admin_password="$(secret)"
eda_pg_password="$(secret)"
metrics_pg_password="$(secret)"
metrics_read_password="$(secret)"

log "Writing the growth all-in-one inventory"
cat >"${installer_dir}/inventory-growth" <<EOF
[automationgateway]
${FQDN}
[automationcontroller]
${FQDN}
[automationhub]
${FQDN}
[automationeda]
${FQDN}
[automationmetrics]
${FQDN}
[database]
${FQDN}

[all:vars]
ansible_connection=local
postgresql_admin_username=postgres
postgresql_admin_password=${postgres_password}
bundle_install=true
bundle_dir='{{ lookup("ansible.builtin.env", "PWD") }}/bundle'
container_pull_images=false
redis_mode=standalone
gateway_admin_password=${gateway_admin_password}
gateway_pg_host=${FQDN}
gateway_pg_password=${gateway_pg_password}
controller_admin_password=${controller_admin_password}
controller_pg_host=${FQDN}
controller_pg_password=${controller_pg_password}
controller_percent_memory_capacity=0.5
hub_admin_password=${hub_admin_password}
hub_pg_host=${FQDN}
hub_pg_password=${hub_pg_password}
hub_seed_collections=false
eda_admin_password=${eda_admin_password}
eda_pg_host=${FQDN}
eda_pg_password=${eda_pg_password}
automationmetrics_pg_host=${FQDN}
automationmetrics_pg_password=${metrics_pg_password}
automationmetrics_controller_read_pg_host=${FQDN}
automationmetrics_controller_read_pg_password=${metrics_read_password}
EOF
chown "$AAP_USER:$AAP_USER" "${installer_dir}/inventory-growth"
chmod 0600 "${installer_dir}/inventory-growth"

cat >"$LOGIN_FILE" <<EOF
AAP URL: https://${FQDN}
AAP IP: ${HOST_IP}
Username: admin
Password: ${gateway_admin_password}
Client hosts entry: ${HOST_IP} ${FQDN} ${FQDN%%.*}
EOF
chmod 0600 "$LOGIN_FILE"

log "Configuring firewall access"
systemctl enable --now firewalld
firewall-cmd --permanent --add-service=http
firewall-cmd --permanent --add-service=https
firewall-cmd --reload

log "Running AAP containerized installer (this can take 30-60 minutes)"
runtime_dir="/run/user/${user_uid}"
runuser -u "$AAP_USER" -- env \
  HOME="$AAP_HOME" USER="$AAP_USER" LOGNAME="$AAP_USER" \
  XDG_RUNTIME_DIR="$runtime_dir" DBUS_SESSION_BUS_ADDRESS="unix:path=${runtime_dir}/bus" \
  bash -c 'cd "$1" && ansible-playbook -i inventory-growth ansible.containerized_installer.install' \
  bash "$installer_dir"

log "Verifying services and authenticated web access"
if runuser -u "$AAP_USER" -- env HOME="$AAP_HOME" XDG_RUNTIME_DIR="$runtime_dir" \
  DBUS_SESSION_BUS_ADDRESS="unix:path=${runtime_dir}/bus" \
  systemctl --user --failed --no-legend | grep -q .; then
  die "One or more AAP user services failed."
fi
curl --retry 12 --retry-delay 10 --retry-all-errors -kfsS \
  "https://${FQDN}/" >/dev/null
curl --retry 6 --retry-delay 5 --retry-all-errors -kfsS \
  -u "admin:${gateway_admin_password}" \
  "https://${FQDN}/api/gateway/v1/me/" >/dev/null

trap - ERR
log "AAP installation completed successfully."
cat "$LOGIN_FILE"
printf '\nAdd the displayed hosts entry to the computer used to open the AAP web interface.\n'
