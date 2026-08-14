#!/usr/bin/env python3
"""Generate direct Community Ansible inventory from canonical lab inventory."""

from copy import deepcopy
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "automation/inventories/lab/hosts.yml"
DESTINATION = ROOT / "automation/inventories/pnetlab/hosts.yml"

GROUP_VARS = {
    "arista_eos": {"ansible_connection": "ansible.netcommon.network_cli", "ansible_network_os": "arista.eos.eos", "ansible_user": "admin"},
    "cisco_ios": {"ansible_connection": "ansible.netcommon.network_cli", "ansible_network_os": "cisco.ios.ios", "ansible_user": "admin"},
    "cisco_ftd": {"ansible_connection": "ansible.netcommon.network_cli", "ansible_network_os": "cisco.asa.asa", "ansible_user": "admin"},
    "juniper_junos": {"ansible_connection": "ansible.netcommon.netconf", "ansible_network_os": "junipernetworks.junos.junos", "ansible_user": "root"},
    "aruba_aoscx": {"ansible_connection": "ansible.netcommon.network_cli", "ansible_network_os": "arubanetworks.aoscx.aoscx", "ansible_user": "admin"},
    "fortinet_fortios": {"ansible_connection": "ansible.netcommon.httpapi", "ansible_network_os": "fortinet.fortios.fortios", "ansible_user": "admin", "ansible_httpapi_use_ssl": True, "ansible_httpapi_validate_certs": False},
    "linux": {"ansible_connection": "ansible.builtin.ssh", "ansible_user": "root", "ansible_python_interpreter": "auto_silent"},
    "windows": {"ansible_connection": "winrm", "ansible_winrm_transport": "ntlm", "ansible_winrm_scheme": "https", "ansible_winrm_server_cert_validation": "ignore"},
}

def direct_host(source):
    host = deepcopy(source)
    host["ansible_host"] = host["tlb_oob_ip"]
    host["ansible_port"] = {"ssh": 22, "https": 443, "winrm": 5986, "console": 22}[host["tlb_management_protocol"]]
    for key in ("tlb_gateway_port", "tlb_ssh_gateway_port", "tlb_https_gateway_port", "tlb_winrm_gateway_port"):
        host.pop(key, None)
    host.pop("ansible_connection", None)
    if host.get("tlb_vendor_group") == "windows":
        host["ansible_user"] = "Administrator" if host["pnetlab_template"] == "winserver" else "eve"
    return host

def main():
    source = yaml.safe_load(SOURCE.read_text())
    children = source["all"]["children"]
    lab_hosts = children["lab_nodes"]["hosts"]
    output = {"all": {"vars": {
        "ansible_password": "{{ lookup('env', 'TLB_LAB_PASSWORD') }}",
        "ansible_command_timeout": 90,
        "ansible_connect_timeout": 15,
        "tlb_control_node": "MBJ-PRD-ANSIBLE001",
        "tlb_oob_subnet": "10.255.255.0/24",
    }, "children": {
        "pnetlab_control": deepcopy(children["pnetlab_control"]),
        "pnetlab": {"hosts": {name: direct_host(values) for name, values in lab_hosts.items()}},
    }}}
    output_children = output["all"]["children"]
    for group_name, group in children.items():
        if group_name in {"pnetlab_control", "lab_nodes"}:
            continue
        output_children[group_name] = deepcopy(group)
        if group_name in GROUP_VARS:
            output_children[group_name]["vars"] = GROUP_VARS[group_name]
    DESTINATION.parent.mkdir(parents=True, exist_ok=True)
    DESTINATION.write_text("---\n" + yaml.safe_dump(output, sort_keys=False, width=120))
    print(f"wrote {DESTINATION} with {len(lab_hosts)} downstream nodes")

if __name__ == "__main__":
    main()
