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

## Automation management paths

AAP at `192.168.1.251` directly manages only the Community control node at
`192.168.1.250`. `MBJ-PRD-ANSIBLE001` has a second interface at
`10.255.255.125` on `pnet9` and directly manages all 51 downstream nodes by
their isolated OOB reservations. PNETLab at `192.168.1.252` retains its console
fallback for first boot and repair, but its legacy proxy listeners are no longer
the normal AAP management path.

| Service | PNETLab listener | Isolated target |
|---|---:|---:|
| SSH | `31000 + node ID` | `10.255.255.(100 + node ID):22` |
| HTTPS | `32000 + node ID` | `10.255.255.(100 + node ID):443` |
| WinRM | `33000 + node ID` | `10.255.255.(100 + node ID):5986` |

These legacy listeners are retained only for controlled recovery and are not
represented by hosts or inventory sources in AAP.
