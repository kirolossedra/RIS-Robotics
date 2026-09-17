# TS-002 — Husky PS4 Controller Bluetooth Pairing

**Status:** In progress — Bluetooth pairing recovered; controller/input and teleoperation verification pending  
**Date:** 2026-09-17  
**Platform:** Clearpath Husky A200  
**Host:** `husky1`  
**Operating system:** Ubuntu 24.04.4 LTS  
**Controller:** Sony DualShock 4 / PS4 controller  
**Controller identity:** **Husky 3**  
**Controller MAC:** `48:18:8D:52:67:63`  
**Area:** Ethernet access, SSH, Bluetooth controller pairing, and later teleoperation

## Purpose

This record captures the Husky joystick investigation from the point of establishing network access through recovery of the PS4 controller Bluetooth pairing.

The immediate goal is to pair the PS4 controller to the Husky so the robot can later be driven manually during the initial Radar obstacle-footprint data-collection work.

This document deliberately records the full troubleshooting path, not only the successful command, because the failure was caused by state that initially appeared valid: the controller was already shown by BlueZ as paired, bonded, and trusted, yet could not establish a usable HID connection.

## Controller identity

The controller investigated here is physically/logically known as:

```text
Husky 3
```

Its Bluetooth MAC address is:

```text
48:18:8D:52:67:63
```

This mapping should be preserved for future Husky troubleshooting so this controller is not confused with other remembered `Wireless Controller` devices on the robot.

## 1. Ethernet configuration and reachability

The external laptop's Ethernet interface was changed from DHCP/automatic addressing to a manual address on the Husky subnet.

Configuration used:

```text
Laptop Ethernet IPv4: 192.168.131.101
Netmask:               255.255.255.0 (/24)
Gateway:               blank
DNS:                   blank

Husky onboard computer: 192.168.131.1
```

Connectivity was verified with:

```bash
ping 192.168.131.1
```

Observed result:

```text
4 packets transmitted, 4 received, 0% packet loss
rtt min/avg/max/mdev = 0.683/0.870/1.405/0.308 ms
```

This confirmed that the laptop-to-Husky Ethernet path was healthy before Bluetooth troubleshooting began.

## 2. SSH access

The Husky was accessed using:

```bash
ssh robot@192.168.131.1
```

Successful login established the following environment:

```text
Hostname: husky1
OS:       Ubuntu 24.04.4 LTS
Kernel:   6.8.0-111-generic x86_64
User:     robot
```

A stale shell startup reference was also observed:

```text
-bash: /home/administrator/ws/install/setup.bash: No such file or directory
```

This appears unrelated to the Bluetooth pairing failure and was intentionally not modified during this investigation.

## 3. PS4-specific Clearpath path

The controller is a PS4 / DualShock 4 controller, not a PS5 / DualSense controller.

The Husky already had Clearpath's PS4 userspace driver package installed:

```bash
dpkg -l | grep python3-ds4drv
```

Result:

```text
ii  python3-ds4drv  0.8.0-noble  all  Sony DualShock 4 userspace driver for Linux.
```

The controller was put into Bluetooth pairing mode by holding **PS + SHARE** until the light bar rapidly flashed.

The initial Clearpath-friendly pairing command was then run:

```bash
sudo ds4drv-pair
```

Initial result:

```text
** This script must be run as sudo **
Searching for PS4 Controller...
No Controller Found
```

Despite the wording of the first line, the command had in fact been invoked with `sudo`; the important failure was `No Controller Found`.

## 4. Bluetooth adapter verification

The Husky Bluetooth adapter was checked with:

```bash
hciconfig
```

Relevant state:

```text
hci0: Type: Primary  Bus: USB
BD Address: CC:D9:AC:3C:9E:24
UP RUNNING PSCAN
```

This established that the Husky Bluetooth adapter itself was present, powered, running, and scanning-capable. The failure therefore moved away from a missing/down adapter and toward controller discovery or stored pairing state.

## 5. Manual BlueZ discovery

`bluetoothctl` was opened as a diagnostic fallback:

```bash
sudo bluetoothctl
```

The controller reported:

```text
Controller CC:D9:AC:3C:9E:24 Pairable: yes
```

Discovery was started:

```text
scan on
```

The Husky discovered many nearby Bluetooth devices, confirming that Bluetooth scanning was functioning.

After leaving the scan, known controller entries were queried:

```bash
bluetoothctl devices | grep -Ei 'Wireless|Controller|Sony'
```

Result:

```text
Device 48:18:8D:52:67:6C Wireless Controller
Device 70:20:84:58:B6:10 Wireless Controller
Device 48:18:8D:52:67:63 Wireless Controller
```

The device at `48:18:8D:52:67:63` had also appeared actively during scanning with an RSSI of approximately `-56 dBm`, making it the strongest candidate for the nearby controller in hand. This MAC was then confirmed to correspond to the controller known as **Husky 3**.

## 6. Existing stored state for Husky 3

The controller record was inspected:

```bash
bluetoothctl info 48:18:8D:52:67:63
```

BlueZ reported:

```text
Name: Wireless Controller
Alias: Wireless Controller
Icon: input-gaming
Paired: yes
Bonded: yes
Trusted: yes
Blocked: no
Connected: no
WakeAllowed: yes
LegacyPairing: no
UUID: Human Interface Device
UUID: PnP Information
Modalias: usb:v054Cp09CCd0100
```

This was an important observation: from BlueZ's stored state, the controller appeared correctly known to the Husky.

However, it was not connected.

## 7. Failed reconnect despite valid-looking bond

A direct reconnect was attempted:

```bash
bluetoothctl connect 48:18:8D:52:67:63
```

Result:

```text
Attempting to connect to 48:18:8D:52:67:63
[CHG] Device 48:18:8D:52:67:63 Connected: yes
Failed to connect: org.bluez.Error.Failed br-connection-create-socket
```

The device briefly transitioned to `Connected: yes`, but the connection failed while BlueZ was creating the BR/EDR connection socket.

A subsequent check showed:

```text
Paired: yes
Trusted: yes
Connected: no
```

Therefore the controller was not remaining connected.

## 8. Working hypothesis

At this point the evidence indicated that the problem was not:

- Ethernet connectivity;
- SSH access;
- a missing Bluetooth adapter;
- the Bluetooth adapter being down;
- the absence of `python3-ds4drv`;
- inability of the Husky to perform Bluetooth discovery; or
- complete inability to see the controller.

Instead, the stored controller state was internally inconsistent with the actual usable connection state:

```text
BlueZ record
  Paired: yes
  Bonded: yes
  Trusted: yes
        |
        v
BR/EDR link begins
        |
        v
Connected: yes (briefly)
        |
        v
HID/socket establishment fails
        |
        v
br-connection-create-socket
        |
        v
Connected: no
```

The leading hypothesis was therefore a **stale or otherwise unusable existing Bluetooth bond** between the Husky and Husky 3.

This diagnosis is strongly supported by the recovery sequence below, but the precise low-level security/socket failure was **not directly proven**. A packet/controller trace such as `btmon` during the failed connection would have been required to prove exactly which Bluetooth handshake or stored-key condition failed.

## 9. Remove the existing bond

The existing Husky 3 record was explicitly deleted:

```bash
bluetoothctl remove 48:18:8D:52:67:63
```

Result:

```text
[DEL] Device 48:18:8D:52:67:63 Wireless Controller
Device has been removed
```

This deliberately forced the next attempt to create a new bond rather than reuse the apparently valid but unusable stored one.

## 10. Fresh pairing

The PS4 controller was again placed into pairing mode with **PS + SHARE**.

Then the Clearpath PS4 pairing command was retried:

```bash
sudo ds4drv-pair
```

This time it immediately found Husky 3 and performed a complete new pairing sequence:

```text
Searching for PS4 Controller...
trust 48:18:8D:52:67:63
Changing 48:18:8D:52:67:63 trust succeeded
pair 48:18:8D:52:67:63
Attempting to pair with 48:18:8D:52:67:63
[CHG] Device 48:18:8D:52:67:63 Connected: yes
hci0 new_link_key 48:18:8D:52:67:63 type 0x04 pin_len 0 store_hint 1
[CHG] Device 48:18:8D:52:67:63 Bonded: yes
[CHG] Device 48:18:8D:52:67:63 WakeAllowed: yes
[CHG] Device 48:18:8D:52:67:63 ServicesResolved: yes
[CHG] Device 48:18:8D:52:67:63 Paired: yes
Pairing successful
```

The most important new event is:

```text
hci0 new_link_key 48:18:8D:52:67:63
```

A fresh Bluetooth link key was created, followed by successful bonding, service resolution, and pairing.

## 11. Root-cause assessment

### Confirmed facts

The following are directly supported by the observed logs:

1. Husky 3 is `48:18:8D:52:67:63`.
2. Before repair, BlueZ considered it paired, bonded, and trusted.
3. A reconnect briefly reached `Connected: yes` but failed with `br-connection-create-socket` and returned to `Connected: no`.
4. Removing the stored device record deleted the previous bond.
5. Re-entering PS4 pairing mode and running `ds4drv-pair` generated a **new link key**.
6. The fresh bond completed successfully with `Bonded: yes`, `ServicesResolved: yes`, `Paired: yes`, and `Pairing successful`.

### Best-supported diagnosis

The previous Husky 3 Bluetooth bond was **stale, inconsistent, or otherwise unusable for establishing the controller's BR/EDR HID connection**.

The repair was:

```text
remove old BlueZ device/bond
        -> put Husky 3 into pairing mode
        -> run ds4drv-pair
        -> negotiate a new Bluetooth link key
        -> resolve HID services
        -> pairing succeeds
```

### What is not proven

The logs do not prove exactly why the old bond had become unusable. Possible low-level causes include stale link-key/security state or another BlueZ BR/EDR HID reconnection problem, but naming one of these as the exact mechanism would overstate the evidence available from this session.

The operational conclusion is therefore intentionally narrower:

> Husky 3 had an existing BlueZ bond that appeared valid but could not establish a stable usable connection. Deleting the existing record and performing a clean `ds4drv-pair` generated a new link key and restored successful pairing.

## 12. Troubleshooting procedure established for this Husky

If Husky 3 later appears as paired/trusted but cannot reconnect, use this investigation order rather than immediately assuming hardware failure:

```text
1. Verify hci0 is UP/RUNNING
2. Confirm python3-ds4drv is installed
3. Confirm controller identity: Husky 3 = 48:18:8D:52:67:63
4. Inspect bluetoothctl info for Paired / Bonded / Trusted / Connected
5. Attempt connection and capture the exact BlueZ error
6. If the old bond is clearly unusable, remove the device record
7. Put controller into PS + SHARE pairing mode
8. Run sudo ds4drv-pair
9. Verify a fresh bond/link key is created
10. Verify controller input and ROS teleoperation separately
```

Do not repeatedly remove/re-pair the controller as a generic first step. The stored bond should be reset when the evidence indicates that the existing bond is the failing layer.

## Current state

At the end of this part of the investigation:

- Laptop Ethernet: **configured and working**
- Husky IP: **`192.168.131.1` reachable**
- SSH as `robot`: **working**
- Bluetooth adapter `hci0`: **UP / RUNNING**
- PS4 driver package `python3-ds4drv`: **installed**
- Controller: **Husky 3**
- Husky 3 MAC: **`48:18:8D:52:67:63`**
- Previous Bluetooth bond: **removed after failed reconnect**
- Fresh Bluetooth link key: **created**
- Fresh pairing: **successful**
- HID services: **resolved during pairing**
- Persistent controller connection after pairing: **not yet independently verified**
- Linux joystick/input device behavior: **not yet verified**
- ROS joystick topic: **not yet verified**
- Husky teleoperation from PS4 controller: **not yet verified**

The next investigation step should begin from controller/input verification rather than repeating Ethernet or pairing work that has already been established.
