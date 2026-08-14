# Inventory Design

Every downstream host has a stable name, OOB address, management protocol,
PNETLab template, site, role, and vendor group in the canonical inventory. The
generated direct inventory defines transport defaults at platform group level
and credentials only through `TLB_LAB_PASSWORD` at execution time.

The `pnetlab` group contains exactly 51 hosts. Children provide platform groups
for Linux, Windows, Arista EOS, Cisco IOS and FTD, Junos, Aruba AOS-CX,
FortiOS, PAN-OS, Infoblox NIOS, and VPCS. `pnetlab_control` describes the
PNETLab host and is not part of downstream execution.

Do not hand-edit the generated inventory. Update the canonical lab inventory,
run `python3 automation/tools/build_community_inventory.py`, review the diff,
and run `ansible-inventory --graph` before committing.
