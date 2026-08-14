# Removing Nodes

Power off or isolate the intended PNETLab node, then remove its canonical host
entry and all group references from `automation/inventories/lab/hosts.yml`.
Regenerate the direct inventory and verify the host no longer appears in
`ansible-inventory --graph`.

Remove the node from the PNETLab topology only after confirming the node ID,
name, disk ownership, and required recovery retention. Commit and push the
topology and inventory changes. No AAP host deletion is normally required
because downstream nodes are not represented in AAP.
