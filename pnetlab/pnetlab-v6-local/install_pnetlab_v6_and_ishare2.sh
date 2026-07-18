#!/usr/bin/env bash

# Zero-touch PNETLab 6.0.0-103 + iShare2 installer for Ubuntu 20.04 AMD64.
# Place this script beside the existing packages/ directory and run it as root.
# It uses the iShare2 defaults and automatically schedules the required reboot.

set -Eeuo pipefail
IFS=$'\n\t'
umask 022

export LC_ALL=C
export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE=a

readonly EXPECTED_UBUNTU_VERSION="20.04"
readonly EXPECTED_ARCH="amd64"
readonly PNETLAB_VERSION="6.0.0-103"
readonly CUSTOM_KERNEL="5.17.15-pnetlab-uksm-2"
readonly ISHARE2_URL="https://raw.githubusercontent.com/ishare2-org/ishare2-cli/main/ishare2"
readonly SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly PACKAGE_DIR="${PNETLAB_PACKAGE_DIR:-${SCRIPT_DIR}/packages}"
readonly AUTO_REBOOT="${PNETLAB_AUTO_REBOOT:-1}"
readonly LOG_FILE="/var/log/pnetlab-ishare2-install.log"

readonly KERNEL_ZIP="pnetlab_kernel.zip"
readonly PRE_DOCKER_ZIP="pre-docker.zip"
readonly TPM_ZIP="swtpm-focal.zip"
readonly GUACAMOLE_DEB="pnetlab-guacamole_6.0.0-7_amd64.deb"
readonly DYNAMIPS_DEB="pnetlab-dynamips_6.0.0-30_amd64.deb"
readonly SCHEMA_DEB="pnetlab-schema_6.0.0-30_amd64.deb"
readonly VPCS_DEB="pnetlab-vpcs_6.0.0-30_amd64.deb"
readonly QEMU_DEB="pnetlab-qemu_6.0.0-30_amd64.deb"
readonly DOCKER_DEB="pnetlab-docker_6.0.0-30_amd64.deb"
readonly PNETLAB_DEB="pnetlab_6.0.0-103_amd64.deb"
readonly WIRESHARK_DEB="pnetlab-wireshark_6.0.0-30_amd64.deb"

readonly -a REQUIRED_FILES=(
    "$KERNEL_ZIP" "$PRE_DOCKER_ZIP" "$TPM_ZIP" "$GUACAMOLE_DEB"
    "$DYNAMIPS_DEB" "$SCHEMA_DEB" "$VPCS_DEB" "$QEMU_DEB"
    "$DOCKER_DEB" "$PNETLAB_DEB" "$WIRESHARK_DEB"
)

readonly -a APT_GET=(
    apt-get
    -o DPkg::Lock::Timeout=300
    -o Dpkg::Options::=--force-confdef
    -o Dpkg::Options::=--force-confold
)

GREEN='\033[32m'
RED='\033[31m'
YELLOW='\033[33m'
NO_COLOR='\033[0m'
WORK_DIR=""
CURRENT_STEP="initial checks"
VALIDATED_LOCAL_DEBS=()

info() { printf '%b%s%b\n' "$GREEN" "$*" "$NO_COLOR"; }
warn() { printf '%bWARNING: %s%b\n' "$YELLOW" "$*" "$NO_COLOR" >&2; }
fail() { printf '%bERROR: %s%b\n' "$RED" "$*" "$NO_COLOR" >&2; exit 1; }

cleanup() {
    if [[ -n "$WORK_DIR" && -d "$WORK_DIR" && "$WORK_DIR" == /tmp/pnetlab-v6-install.* ]]; then
        find "$WORK_DIR" -depth -delete 2>/dev/null || true
    fi
}

on_error() {
    local exit_code=$?
    local line_number="${BASH_LINENO[0]:-unknown}"
    printf '%bERROR: Step "%s" failed at line %s (exit %s). See %s.%b\n' \
        "$RED" "$CURRENT_STEP" "$line_number" "$exit_code" "$LOG_FILE" "$NO_COLOR" >&2
    exit "$exit_code"
}

trap cleanup EXIT
trap on_error ERR

[[ "$(id -u)" -eq 0 ]] || fail "Run this installer as root: sudo ./$(basename "$0")"

mkdir -p "$(dirname "$LOG_FILE")"
touch "$LOG_FILE"
chmod 600 "$LOG_FILE"
exec > >(tee -a "$LOG_FILE") 2>&1

if command -v flock >/dev/null 2>&1; then
    exec 9>/var/lock/pnetlab-v6-installer.lock
    flock -n 9 || fail "Another copy of this installer is already running."
fi
WORK_DIR="$(mktemp -d /tmp/pnetlab-v6-install.XXXXXX)"

apt_update() { "${APT_GET[@]}" update; }
apt_install() { "${APT_GET[@]}" install -y --no-remove "$@"; }
package_status() { dpkg-query -W -f='${Status}' "$1" 2>/dev/null || true; }

verify_deb_installed() {
    local deb_path="$1"
    local package_name package_version installed_status installed_version
    package_name="$(dpkg-deb -f "$deb_path" Package)"
    package_version="$(dpkg-deb -f "$deb_path" Version)"
    installed_status="$(package_status "$package_name")"
    installed_version="$(dpkg-query -W -f='${Version}' "$package_name" 2>/dev/null || true)"
    [[ "$installed_status" == "install ok installed" ]] || \
        fail "$package_name was not completely installed from $(basename "$deb_path")."
    [[ "$installed_version" == "$package_version" ]] || \
        fail "$package_name version $installed_version is installed; expected $package_version."
}

install_local_deb() {
    local filename="$1"
    local description="$2"
    local deb_path="$PACKAGE_DIR/$filename"
    CURRENT_STEP="installing $description"
    info "Installing $description..."
    apt_install "$deb_path"
    verify_deb_installed "$deb_path"
    VALIDATED_LOCAL_DEBS+=("$deb_path")
}

was_validated_this_run() {
    local requested_path="$1"
    local validated_path
    for validated_path in "${VALIDATED_LOCAL_DEBS[@]}"; do
        [[ "$validated_path" == "$requested_path" ]] && return 0
    done
    return 1
}

install_debs_from_zip() {
    local zip_name="$1"
    local description="$2"
    local destination="$WORK_DIR/${zip_name%.zip}"
    local deb
    local -a debs=()
    CURRENT_STEP="installing $description"
    mkdir -p "$destination"
    unzip -q "$PACKAGE_DIR/$zip_name" -d "$destination"
    while IFS= read -r -d '' deb; do
        dpkg-deb --info "$deb" >/dev/null
        debs+=("$deb")
    done < <(find "$destination" -type f -name '*.deb' -print0 | sort -z)
    ((${#debs[@]} > 0)) || fail "No Debian packages were found inside $zip_name."
    info "Installing $description..."
    apt_install "${debs[@]}"
    for deb in "${debs[@]}"; do verify_deb_installed "$deb"; done
}

configure_mysql_root() {
    CURRENT_STEP="configuring MySQL for PNETLab"
    info "Configuring MySQL authentication required by PNETLab..."
    systemctl enable --now mysql
    if mysql --protocol=socket -uroot -Nse 'SELECT 1' >/dev/null 2>&1; then
        mysql --protocol=socket -uroot <<'SQL'
ALTER USER 'root'@'localhost' IDENTIFIED WITH mysql_native_password BY 'pnetlab';
FLUSH PRIVILEGES;
SQL
    elif ! mysql -uroot -ppnetlab -Nse 'SELECT 1' >/dev/null 2>&1; then
        fail "MySQL root authentication is neither fresh socket authentication nor the PNETLab password."
    fi
    mysql -uroot -ppnetlab -Nse 'SELECT 1' >/dev/null || \
        fail "MySQL did not accept the root password required by PNETLab."
}

verify_service() {
    local service_name="$1"
    systemctl enable "$service_name" >/dev/null
    systemctl restart "$service_name"
    systemctl is-active --quiet "$service_name" || fail "$service_name is not active."
}

CURRENT_STEP="checking the operating system"
[[ -r /etc/os-release ]] || fail "/etc/os-release is unavailable."
# shellcheck disable=SC1091
source /etc/os-release
[[ "${ID:-}" == "ubuntu" && "${VERSION_ID:-}" == "$EXPECTED_UBUNTU_VERSION" ]] || \
    fail "This installer requires Ubuntu $EXPECTED_UBUNTU_VERSION; detected ${PRETTY_NAME:-unknown}."
[[ "$(dpkg --print-architecture)" == "$EXPECTED_ARCH" ]] || \
    fail "These packages require $EXPECTED_ARCH; detected $(dpkg --print-architecture)."
case "$AUTO_REBOOT" in 0|1) ;; *) fail "PNETLAB_AUTO_REBOOT must be 0 or 1." ;; esac

info "Using local PNETLab packages from: $PACKAGE_DIR"
missing=0
for filename in "${REQUIRED_FILES[@]}"; do
    if [[ ! -s "$PACKAGE_DIR/$filename" ]]; then
        printf '%bMissing or empty: %s%b\n' "$RED" "$PACKAGE_DIR/$filename" "$NO_COLOR" >&2
        missing=1
    fi
done
((missing == 0)) || fail "The complete eleven-file local PNETLab bundle is required."

CURRENT_STEP="installing validation and repository tools"
apt_update
apt_install ca-certificates curl wget gnupg lsb-release mokutil unzip zip \
    software-properties-common debconf-utils openssh-server util-linux
add-apt-repository -y universe >/dev/null
add-apt-repository -y multiverse >/dev/null
apt_update

CURRENT_STEP="validating Secure Boot"
if [[ -d /sys/firmware/efi ]]; then
    secure_boot_state="$(mokutil --sb-state 2>&1 || true)"
    case "$secure_boot_state" in
        *"SecureBoot disabled"*|*"Setup Mode"*) info "UEFI Secure Boot is disabled." ;;
        *"SecureBoot enabled"*) fail "Disable UEFI Secure Boot before installing the unsigned PNETLab kernel." ;;
        *) fail "Could not verify Secure Boot state: $secure_boot_state" ;;
    esac
else
    info "The server uses legacy BIOS; Secure Boot does not apply."
fi

CURRENT_STEP="validating the local PNETLab bundle"
info "Validating all local archives..."
for archive in "$KERNEL_ZIP" "$PRE_DOCKER_ZIP" "$TPM_ZIP"; do
    unzip -tq "$PACKAGE_DIR/$archive" >/dev/null
done
for package in "$GUACAMOLE_DEB" "$DYNAMIPS_DEB" "$SCHEMA_DEB" "$VPCS_DEB" \
    "$QEMU_DEB" "$DOCKER_DEB" "$PNETLAB_DEB" "$WIRESHARK_DEB"; do
    dpkg-deb --info "$PACKAGE_DIR/$package" >/dev/null
done
info "All eleven local files passed structural validation."

if ! grep -Eq '(^|[[:space:]])(vmx|svm)([[:space:]]|$)' /proc/cpuinfo; then
    warn "Intel VT-x/AMD-V is not exposed; hardware-accelerated nodes will not run."
fi

CURRENT_STEP="repairing any interrupted package state"
if ! dpkg --configure -a; then
    "${APT_GET[@]}" install -f -y --no-remove
    dpkg --configure -a
fi

CURRENT_STEP="installing base PNETLab prerequisites"
info "Installing base PNETLab and iShare2 prerequisites..."
apt_install ifupdown resolvconf mysql-server apache2 php7.4 php7.4-cli php7.4-common \
    php7.4-curl php7.4-gd php7.4-mbstring php7.4-mysql php7.4-sqlite3 \
    php7.4-xml php7.4-zip php-imagick php-yaml libapache2-mod-php7.4 \
    curl wget jq unrar tree unzip dos2unix lvm2 rsync sshpass net-tools
update-alternatives --set php /usr/bin/php7.4

if [[ ! -e /opt/ovf/.configured ]]; then echo 'root:pnet' | chpasswd; fi

# Ubuntu 20.04 uses MySQL 8 socket authentication. PNETLab's Guacamole and
# main-package pre-install scripts require mysql -uroot -ppnetlab instead.
configure_mysql_root

CURRENT_STEP="replacing systemd-timesyncd with the PNETLab NTP service"
# PNETLab 6 explicitly depends on the classic ntp package. On Ubuntu 20.04,
# ntp conflicts with the default systemd-timesyncd package. Install the new
# time provider in the same transaction that removes the old provider so the
# time-daemon dependency remains continuously satisfied. Refuse the plan if
# APT proposes removing anything else.
if [[ "$(package_status systemd-timesyncd)" == "install ok installed" ]]; then
    info "Replacing systemd-timesyncd with the NTP service required by PNETLab..."
    ntp_plan="$("${APT_GET[@]}" --simulate install ntp ntpdate)"
    unexpected_removals="$(awk '/^Remv / && $2 != "systemd-timesyncd" {print $2}' <<< "$ntp_plan")"
    [[ -z "$unexpected_removals" ]] || \
        fail "The NTP replacement would remove unexpected packages: $unexpected_removals"
    grep -Eq '^Remv systemd-timesyncd([[:space:]]|$)' <<< "$ntp_plan" || \
        fail "APT did not produce the expected systemd-timesyncd replacement plan."
    "${APT_GET[@]}" install -y ntp ntpdate
else
    apt_install ntp ntpdate
fi
systemctl enable ntp >/dev/null
systemctl restart ntp
systemctl is-active --quiet ntp || fail "The NTP service required by PNETLab is not active."

CURRENT_STEP="removing conflicting distribution Docker packages"
conflicting_docker_packages=()
for candidate in docker.io containerd runc; do
    if [[ "$(package_status "$candidate")" == "install ok installed" ]]; then
        conflicting_docker_packages+=("$candidate")
    fi
done
if ((${#conflicting_docker_packages[@]} > 0)); then
    "${APT_GET[@]}" purge -y "${conflicting_docker_packages[@]}"
fi

install_debs_from_zip "$KERNEL_ZIP" "the PNETLab custom kernel"
install_debs_from_zip "$PRE_DOCKER_ZIP" "the PNETLab Docker prerequisites"
install_debs_from_zip "$TPM_ZIP" "the PNETLab software TPM prerequisites"

# Order follows the packages' Pre-Depends and maintainer scripts.
install_local_deb "$SCHEMA_DEB" "PNETLab schema 6.0.0-30"
configure_mysql_root
install_local_deb "$DOCKER_DEB" "PNETLab Docker 6.0.0-30"
install_local_deb "$GUACAMOLE_DEB" "PNETLab Guacamole 6.0.0-7"
install_local_deb "$VPCS_DEB" "PNETLab VPCS 6.0.0-30"
install_local_deb "$DYNAMIPS_DEB" "PNETLab Dynamips 6.0.0-30"
install_local_deb "$WIRESHARK_DEB" "PNETLab Wireshark 6.0.0-30"
install_local_deb "$QEMU_DEB" "PNETLab QEMU 6.0.0-30"
install_local_deb "$PNETLAB_DEB" "PNETLab $PNETLAB_VERSION"

CURRENT_STEP="finishing PNETLab configuration"
dpkg --configure -a
update-initramfs -u -k all
update-grub
[[ -x /opt/unetlab/wrappers/unl_wrapper ]] || fail "The PNETLab wrapper was not installed."
/opt/unetlab/wrappers/unl_wrapper -a fixpermissions

info "Starting and verifying PNETLab services..."
for service_name in mysql docker guacd tomcat9 apache2; do verify_service "$service_name"; done

CURRENT_STEP="verifying PNETLab"
verify_deb_installed "$PACKAGE_DIR/$PNETLAB_DEB"
for package in "$SCHEMA_DEB" "$DOCKER_DEB" "$GUACAMOLE_DEB" "$VPCS_DEB" \
    "$DYNAMIPS_DEB" "$WIRESHARK_DEB" "$QEMU_DEB"; do
    deb_path="$PACKAGE_DIR/$package"
    package_name="$(dpkg-deb -f "$deb_path" Package)"
    if [[ "$(package_status "$package_name")" == "install ok installed" ]]; then
        verify_deb_installed "$deb_path"
    elif was_validated_this_run "$deb_path"; then
        warn "$package_name was installed, then superseded by the main PNETLab package."
    else
        fail "$package_name is absent and was not validated during this run."
    fi
done

for kernel_package in "linux-image-$CUSTOM_KERNEL" "linux-headers-$CUSTOM_KERNEL"; do
    [[ "$(package_status "$kernel_package")" == "install ok installed" ]] || \
        fail "$kernel_package is not installed."
done
[[ -s "/boot/vmlinuz-$CUSTOM_KERNEL" ]] || fail "The PNETLab kernel image is missing."
[[ -s "/boot/initrd.img-$CUSTOM_KERNEL" ]] || fail "The PNETLab initramfs is missing."
[[ -s /opt/unetlab/version ]] || fail "/opt/unetlab/version is missing."
[[ -d /opt/unetlab/html ]] || fail "The PNETLab web application is missing."
mysql -uroot -ppnetlab -Nse \
    "SELECT control_value FROM pnetlab_db.control WHERE control_name='ctrl_version' LIMIT 1" \
    | grep -Fq '6.0.0-103' || fail "The PNETLab database version was not initialized."
if ! curl -kfsSL --max-time 20 https://127.0.0.1/ >/dev/null 2>&1; then
    curl -fsSL --max-time 20 http://127.0.0.1/ >/dev/null || \
        fail "The local PNETLab web interface did not answer."
fi

CURRENT_STEP="installing iShare2"
info "Downloading and installing the current iShare2 main script..."
curl --proto '=https' --tlsv1.2 --fail --location --show-error --silent \
    --retry 5 --retry-delay 2 --connect-timeout 20 --max-time 300 \
    "$ISHARE2_URL" -o "$WORK_DIR/ishare2"
[[ -s "$WORK_DIR/ishare2" ]] || fail "The downloaded iShare2 script is empty."
head -n 1 "$WORK_DIR/ishare2" | grep -Eq '^#!/(usr/)?bin/(env +)?bash' || \
    fail "The iShare2 URL did not return a Bash script."
bash -n "$WORK_DIR/ishare2"
install -o root -g root -m 0755 "$WORK_DIR/ishare2" /usr/sbin/ishare2

# The official CLI's --init path accepts its documented defaults. Supply blank
# answers so the run stays noninteractive if more defaulted prompts are added.
mkdir -p /opt/ishare2/cli
defaults_input="$WORK_DIR/ishare2-default-answers"
for _ in $(seq 1 64); do printf '\n'; done > "$defaults_input"
/usr/sbin/ishare2 --init < "$defaults_input"

CURRENT_STEP="verifying iShare2"
[[ -x /usr/sbin/ishare2 ]] || fail "iShare2 is not executable."
[[ -s /opt/ishare2/cli/ishare2.conf ]] || fail "iShare2 did not create its configuration."
grep -Eq '^USE_ARIA2C=false$' /opt/ishare2/cli/ishare2.conf || \
    fail "iShare2 did not retain its default aria2c setting."
grep -Eq '^SSL_CHECK=(true|"true")$' /opt/ishare2/cli/ishare2.conf || \
    fail "iShare2 did not retain its default SSL setting."
grep -Eq '^ROTATE=true$' /opt/ishare2/cli/ishare2.conf || \
    fail "iShare2 did not retain its default mirror rotation setting."
timeout 90 /usr/sbin/ishare2 --version >/dev/null

CURRENT_STEP="final package audit"
audit_output="$(dpkg --audit)"
[[ -z "$audit_output" ]] || fail "dpkg reports incomplete packages: $audit_output"
"${APT_GET[@]}" autoclean -y >/dev/null || warn "apt-get autoclean reported an error."

info "PNETLab $PNETLAB_VERSION and iShare2 installed and verified successfully."
info "PNETLab initial credentials: username=root password=pnet"
info "Full installation log: $LOG_FILE"

if [[ "$(uname -r)" != "$CUSTOM_KERNEL" ]]; then
    if [[ "$AUTO_REBOOT" == "1" ]]; then
        info "The server will reboot automatically in one minute into $CUSTOM_KERNEL."
        shutdown -r +1 "PNETLab installation complete; rebooting into the PNETLab kernel"
    else
        warn "A reboot into $CUSTOM_KERNEL is required; automatic reboot was disabled."
    fi
else
    info "The server already runs the PNETLab kernel; no reboot is needed."
fi
