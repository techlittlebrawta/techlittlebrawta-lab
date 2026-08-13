# Tech Little Brawta PNETLab

The canonical topology is `pnetlab/topologies/tech-little-brawta-lab.unl`.
It is sanitized for public storage: controller and device secrets are held in
AAP credentials and are not embedded in the repository copy.

## Layout

- Montego Bay is the primary data center at the top of the canvas.
- New York, Manilla, and Barcelona are the lower-left, lower-middle, and
  lower-right remote sites.
- Shared application, identity, security, voice, and logging platforms are
  workloads inside Montego Bay rather than a separate site.
- Every endpoint has one visible production cable to its local access switch.
- The isolated management network is `pnet9` (`10.255.255.0/24`) and is hidden
  from the presentation topology.

## AAP management path

AAP at `192.168.1.251` never assigns lab appliances addresses on the private
LAN. It reaches PNETLab at `192.168.1.252`, which proxies SSH, HTTPS, and WinRM
to isolated OOB reservations. Every node also has a PNETLab-console fallback,
so first-boot and devices without a ready management service remain manageable.

| Service | PNETLab listener | Isolated target |
|---|---:|---:|
| SSH | `31000 + node ID` | `10.255.255.(100 + node ID):22` |
| HTTPS | `32000 + node ID` | `10.255.255.(100 + node ID):443` |
| WinRM | `33000 + node ID` | `10.255.255.(100 + node ID):5986` |

Only AAP is permitted to use these listeners.
