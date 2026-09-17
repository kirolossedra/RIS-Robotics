# TS-001 — Husky Onboard Computer Not Powering Up

**Status:** Resolved  
**Date:** 2026-09-17  
**Platform:** Clearpath Husky A200  
**Area:** Robot-side power and connectivity  
**Initial symptom:** Ethernet connection to the Husky was not detected

## Purpose

This record captures the first Husky troubleshooting session in the RIS Robotics project. The immediate goal was to connect to the Husky so that later work could pair a controller and use the robot as a simple moving or stationary obstacle for Radar obstacle-footprint data collection.

The first apparent problem was Ethernet connectivity. Investigation showed that the Ethernet failure was downstream of a more basic fault: the Husky onboard computer was not powered.

## Initial symptom

The laptop did not detect an Ethernet connection to the Husky.

Before investigating IP configuration, SSH, ROS, controller pairing, or any higher-level software, the physical Husky computer was inspected.

The onboard computer showed no signs of power.

This changed the troubleshooting path from:

```text
Ethernet / IP / SSH / ROS
```

to:

```text
Husky power distribution
        -> onboard-computer power
        -> Ethernet physical link
        -> networking
```

## Husky A200 user-power panel observations

The Husky user-power panel exposes three labeled power rails:

- **24 V / 5 A** — red section
- **12 V / 5 A** — green section
- **5 V / 5 A** — gray section

The onboard computer was independently verified to require **12 V DC**, making the green `12 V / 5 A` rail the relevant supply.

The 24 V output was therefore explicitly excluded from the computer-power path.

## Existing wiring discovered

The installed wiring is not a simple untouched stock computer-power cable. The 12 V connection uses a modified/split harness.

Observed path:

```text
Husky green 12 V / 5 A outlet
            |
            v
      red/black harness
            |
       +----+----+
       |    |    |
       v    v    v
   barrel barrel different power lead
   output  output        |
                         v
                  onboard computer
```

Two loose DC barrel-style outputs were present on the 12 V harness. A separate power connector of a different physical type was already attached to the onboard computer.

The blue USB cable in the bay is separate from computer power and is associated with the Husky MCU/computer connection.

The yellow Ethernet cable was connected to the onboard computer, but Ethernet could not become active while the computer itself was unpowered.

## Photo evidence

The following are the actual photos captured during this troubleshooting session. They are stored with this incident and rendered here using repository-relative paths.

### 1. Husky user-power panel

![Husky A200 user-power panel showing the 24 V, 12 V and 5 V rails](images/TS-001/01-husky-user-power-panel.jpg)

The relevant computer supply was identified as the green **12 V / 5 A** rail. The computer had separately been confirmed to require 12 V.

### 2. Onboard computer and DC input

![Husky onboard computer and its connected DC power input](images/TS-001/02-onboard-computer-and-dc-input.jpg)

The onboard computer had a power connector physically attached, despite showing no sign of power. This was important because a seated connector initially made a disconnected power path appear less likely.

### 3. 12 V harness overview

![Overview of the Husky 12 V harness and onboard computer wiring](images/TS-001/03-12v-harness-overview.jpg)

This view established that the installed power wiring is a modified/split harness rather than the simplest stock single-output arrangement.

### 4. Split-harness connector detail

![Close view of the two loose barrel outputs from the Husky 12 V split harness](images/TS-001/04-12v-split-harness-connectors.jpg)

Two loose barrel-style outputs were present on the same 12 V harness while a different connector branch was already feeding the onboard computer. The loose barrel outputs were therefore not, by themselves, proof that the computer power lead was missing.

These photos document the physical state **before the final root cause was identified: reversed polarity on the computer's 12 V feed**.

## False leads considered during troubleshooting

Several plausible explanations were considered before the actual root cause was found:

1. The onboard computer power cable might have been completely disconnected.
2. One of the loose barrel connectors might have been the missing computer-power connection.
3. The onboard computer might require manual power-button activation rather than auto-starting.
4. The Husky 12 V rail or its fuse might have failed.
5. The modified power harness might not be delivering power to the computer.

The physical power button on the computer was pressed, but the computer still did not start. This confirmed that the issue was not simply an auto-power/BIOS behavior.

## Root cause

The actual fault was **reversed polarity on the 12 V feed to the onboard computer**.

The connector/harness was physically connected, which made the installation appear complete, but its polarity was wrong.

The polarity was flipped/corrected and the computer powered up successfully.

Therefore the failure chain was:

```text
Ethernet not detected
        |
        v
Onboard computer not running
        |
        v
12 V power path inspected
        |
        v
12 V harness physically connected
        |
        v
Polarity reversed
        |
        v
Computer receives no usable power
```

After correcting polarity:

```text
Correct 12 V polarity
        -> onboard computer powers up
        -> Ethernet hardware can now become active
```

## Resolution

**Resolved by correcting/flipping the polarity of the 12 V computer-power connection.**

No replacement computer, Ethernet cable, ROS configuration, IP configuration, or software change was required to resolve this specific fault.

## Key lesson for this Husky

A connector being physically seated does **not** prove that the power path is correct. On this Husky, the modified 12 V harness can be connected while still presenting the wrong polarity to the computer.

For future work on this robot:

- treat the **green 12 V / 5 A rail** as the onboard-computer supply;
- do not use the 24 V rail for the 12 V computer;
- preserve the now-working polarity/orientation of the computer-power connection;
- if the computer again appears completely dead, inspect the 12 V polarity/orientation before debugging Ethernet, IP, SSH, ROS, or controller pairing;
- the two loose barrel outputs should not be assumed to be required for the computer simply because they are present on the same split harness.

## Troubleshooting hierarchy established

For subsequent Husky connectivity problems, use this order:

```text
1. Husky base powered
2. Onboard computer powered
3. Ethernet physical link
4. IP configuration / reachability
5. SSH / operating-system access
6. ROS and robot interfaces
7. Controller pairing / teleoperation
```

This prevents higher-level debugging from hiding a lower-level physical failure.

## Final state of this incident

- Husky base: **powered**
- Relevant user-power rail: **12 V / 5 A identified**
- Onboard-computer requirement: **12 V confirmed**
- Computer power connector: **physically present**
- Initial power-button attempt: **no startup**
- Root cause: **12 V polarity reversed**
- Fix: **polarity flipped/corrected**
- Onboard computer: **powers up successfully after correction**
- Original Ethernet symptom: **ready for re-evaluation as a separate troubleshooting issue**
