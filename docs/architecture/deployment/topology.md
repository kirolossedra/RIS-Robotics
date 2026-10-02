# Deployment Topology

## Contents

- [Current topology](#current-topology)
- [Target topology](#target-topology)

## Current topology

```text
Radar/RIS -> central DSP host -> USB -> TX nRF52833
TX nRF52833 ~~ BLE ~~ RX nRF52833 -> USB -> RX host
```

The implemented/validated chain currently stops before robot motion control.

## Target topology

```text
DUMMY_ROBOT -> sensing -> DSP -> TX -> BLE -> RX
                                      |
                                      v
                            Controlled Robot-side host
                                      |
                               persistent Ethernet/SSH
                                      |
                                      v
                           CONTROLLED_ROBOT onboard ROS
                                      |
                                 local arbitration
```
