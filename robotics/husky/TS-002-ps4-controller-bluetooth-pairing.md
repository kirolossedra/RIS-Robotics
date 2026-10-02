# TS-002 — Husky PS4 Controller Bluetooth Pairing

> [!IMPORTANT]
> **Controller identity:** **Husky 3 / Joystick 3** = `48:18:8D:52:67:63`. Preserve this mapping. The Husky has multiple remembered devices named `Wireless Controller`, so the MAC address is the reliable identifier.

**Status:** 🟢 Bluetooth pairing recovery validated again on 2026-10-02; ROS-level teleoperation remains a separate verification boundary  
**Original incident:** 2026-09-17  
**Recurrence:** 2026-10-02  
**Platform:** Clearpath Husky A200  
**Host:** `husky1`  
**Operating system:** Ubuntu 24.04.4 LTS  
**Controller:** Sony DualShock 4 / PS4 controller  
**Controller identity:** **Husky 3 / Joystick 3**  
**Controller MAC:** `48:18:8D:52:67:63`  
**Area:** Ethernet access, SSH, Bluetooth controller pairing, and later teleoperation

## Investigation snapshot

| Item | Result |
|---|---|
| Laptop → Husky Ethernet | ✅ Working |
| Husky SSH | ✅ Working |
| Bluetooth adapter `hci0` | ✅ `UP RUNNING PSCAN` |
| `python3-ds4drv` | ✅ Installed |
| Controller identity | ✅ **Husky 3 / Joystick 3** — `48:18:8D:52:67:63` |
| Existing stored bond | ❌ Can look valid but still fail to establish usable connection |
| Failure signature | ⚠️ `br-connection-create-socket` — reproduced 2026-09-17 and 2026-10-02 |
| Old bond removal | ✅ Validated recovery step after failure reproduction |
| Fresh `ds4drv-pair` | ✅ Original incident captured full success transcript; 2026-10-02 recovery operator-confirmed |
| Controller Bluetooth operation | ✅ Working again after 2026-10-02 recovery |
| ROS teleoperation | ⏳ Separate verification boundary |

> [!WARNING]
> **Key recurring failure pattern:** BlueZ can report `Paired: yes`, `Bonded: yes`, and `Trusted: yes` while the controller still cannot establish a usable connection. A valid-looking stored Bluetooth state does **not** prove the bond is usable.

> [!NOTE]
> **Best-supported diagnosis:** the Husky 3 / Joystick 3 Bluetooth bond can become stale, inconsistent, or otherwise unusable for the BR/EDR HID connection. The exact low-level mechanism has not been proven because no `btmon` trace was captured during the failed connection.

## Purpose

This record captures the Husky joystick investigation from the point of establishing network access through recovery of the PS4 controller Bluetooth pairing, including the **2026-10-02 recurrence** of the same failure signature.

The immediate goal is to pair the PS4 controller to the Husky so the robot can be driven manually during the initial Radar obstacle-footprint data-collection work.

This document deliberately records the full troubleshooting path, not only the successful command, because the failure is caused by state that can initially appear valid: the controller can be shown by BlueZ as paired, bonded, and trusted while still failing to establish a usable HID connection.

## Controller identity

> [!IMPORTANT]
> **Husky 3 / Joystick 3** is the controller at Bluetooth MAC **`48:18:8D:52:67:63`**.

The controller investigated here is physically/logically known as Husky 3 / Joystick 3. Its Bluetooth MAC address is:

```text
48:18:8D:52:67:63
```

This mapping must be preserved for future Husky troubleshooting so this controller is not confused with other remembered `Wireless Controller` devices on the robot.

## 1. Original incident — 2026-09-17

### Ethernet configuration and reachability

The external laptop's Ethernet interface was changed from DHCP/automatic addressing to a manual address on the Husky subnet.

```text
Laptop Ethernet IPv4: 192.168.131.101
Netmask:               255.255.255.0 (/24)
Gateway:               blank
DNS:                   blank

Husky onboard computer: 192.168.131.1
```

Connectivity was verified with `ping 192.168.131.1` and SSH with:

```bash
ssh robot@192.168.131.1
```

The Husky environment was:

```text
Hostname: husky1
OS:       Ubuntu 24.04.4 LTS
Kernel:   6.8.0-111-generic x86_64
User:     robot
```

### PS4-specific Clearpath path

The Husky already had the PS4 userspace driver installed:

```text
ii  python3-ds4drv  0.8.0-noble  all  Sony DualShock 4 userspace driver for Linux.
```

The controller was put into Bluetooth pairing mode with **PS + SHARE**, then:

```bash
sudo ds4drv-pair
```

initially returned:

```text
** This script must be run as sudo **
Searching for PS4 Controller...
No Controller Found
```

### Adapter and manual discovery

`hciconfig` showed:

```text
hci0: Type: Primary  Bus: USB
BD Address: CC:D9:AC:3C:9E:24
UP RUNNING PSCAN
```

Manual BlueZ discovery showed multiple remembered `Wireless Controller` devices. The nearby controller was identified as `48:18:8D:52:67:63`, corresponding to Husky 3.

### Stored state looked valid

```bash
bluetoothctl info 48:18:8D:52:67:63
```

reported:

```text
Paired: yes
Bonded: yes
Trusted: yes
Blocked: no
Connected: no
WakeAllowed: yes
LegacyPairing: no
UUID: Human Interface Device
UUID: PnP Information
```

### Direct reconnect failed

```bash
bluetoothctl connect 48:18:8D:52:67:63
```

returned:

```text
Attempting to connect to 48:18:8D:52:67:63
[CHG] Device 48:18:8D:52:67:63 Connected: yes
Failed to connect: org.bluez.Error.Failed br-connection-create-socket
```

This established the central failure pattern: valid-looking stored state, transient connection, then BR/EDR socket failure.

### Original recovery

The old record was removed:

```bash
bluetoothctl remove 48:18:8D:52:67:63
```

The controller was returned to **PS + SHARE** pairing mode and `sudo ds4drv-pair` was run again.

The original 2026-09-17 session captured the complete successful transcript, including:

```text
hci0 new_link_key 48:18:8D:52:67:63 type 0x04 pin_len 0 store_hint 1
Bonded: yes
ServicesResolved: yes
Paired: yes
Pairing successful
```

This proved that the original repair generated a fresh Bluetooth link key and completed a new bond.

## 2. Recurrence — 2026-10-02

### Robot and project state

Husky 1 was powered, laptop-to-Husky communication and SSH worked, and the mounting plate had been mounted back onto the Husky.

The canonical robot-side project root was established as:

```text
/home/robot/robohub/WSDL/kiro
```

BLE joystick logs are stored under:

```text
/home/robot/robohub/WSDL/kiro/logs/BLE/joystick/
```

### Initial pairing attempt

Joystick 3 was placed into rapid-flash PS + SHARE mode and:

```bash
sudo ds4drv-pair
```

again returned:

```text
Searching for PS4 Controller...
No Controller Found
```

### Adapter remained healthy

`hciconfig` showed the same Husky adapter:

```text
BD Address: CC:D9:AC:3C:9E:24
UP RUNNING PSCAN
```

with zero RX/TX errors in the displayed counters.

### Discovery evidence

A first attempt to save a scan with:

```bash
timeout 15s bluetoothctl scan on | tee logs/BLE/joystick/joystick3_scan_2026-10-02.log
```

was inadequate: it wrote only `SetDiscoveryFilter success`. The file was explicitly inspected before drawing conclusions.

The working evidence-capture form was:

```bash
bluetoothctl -m --timeout 15 scan on | tee logs/BLE/joystick/baseline_scan_2026-10-02.log
```

and later, to prevent overwriting:

```bash
bluetoothctl -m --timeout 15 scan on | tee "logs/BLE/joystick/joystick3_scan_$(date +%Y%m%d_%H%M%S).log"
```

With Joystick 3 in pairing mode, the scan saw:

```text
[CHG] Device 48:18:8D:52:67:63 RSSI: -62
```

Therefore the controller was visible to Husky 1 and had not simply disappeared from radio discovery.

### Stored state disproved the erased-pairing hypothesis

```bash
bluetoothctl info 48:18:8D:52:67:63
```

reported:

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

The controller record therefore had **not** been erased. It was the same valid-looking-but-disconnected state seen in the original incident.

### Exact failure reproduced

The direct reconnect was captured to a timestamped log:

```bash
bluetoothctl connect 48:18:8D:52:67:63 | tee "logs/BLE/joystick/joystick3_connect_$(date +%Y%m%d_%H%M%S).log"
```

Result:

```text
Attempting to connect to 48:18:8D:52:67:63
[CHG] Device 48:18:8D:52:67:63 Connected: yes
Failed to connect: org.bluez.Error.Failed br-connection-create-socket
```

This is an exact recurrence of the key 2026-09-17 failure signature.

### Recovery

Only after the failure was reproduced was the old record deliberately removed:

```bash
bluetoothctl remove 48:18:8D:52:67:63 | tee "logs/BLE/joystick/joystick3_remove_$(date +%Y%m%d_%H%M%S).log"
```

The exact removal stdout was not pasted into the 2026-10-02 chat record.

Joystick 3 was then returned to rapid-flash **PS + SHARE** pairing mode and:

```bash
sudo ds4drv-pair
```

was run again.

The operator confirmed that **Joystick 3 was working again** after this clean re-pairing. The final `ds4drv-pair` transcript was not pasted during the 2026-10-02 session, so no specific new-link-key or service-resolution line is claimed for this recurrence.

## 3. Root-cause assessment

### Confirmed across both incidents

1. Joystick 3 / Husky 3 is `48:18:8D:52:67:63`.
2. The Husky Bluetooth adapter remains operational during the failures.
3. BlueZ can report `Paired: yes`, `Bonded: yes`, and `Trusted: yes` while the controller remains unusable.
4. The direct connection can briefly reach `Connected: yes` and then fail with `br-connection-create-socket`.
5. The exact failure occurred on both 2026-09-17 and 2026-10-02.
6. Resetting the stored controller record and cleanly re-pairing restored operation on both occasions.
7. The 2026-09-17 transcript proved a new link key was generated. The 2026-10-02 repair was operator-confirmed working, but the final pairing transcript was not captured in chat.

### Best-supported diagnosis

> [!IMPORTANT]
> The stored Bluetooth bond can become **stale, inconsistent, or otherwise unusable for establishing the DualShock 4 BR/EDR HID connection**, even while BlueZ metadata still reports the controller as paired, bonded, and trusted.

The exact low-level cause remains unproven. A `btmon` capture during a future failure would be required to determine whether the underlying mechanism is specifically link-key/security state, BR/EDR HID socket setup, or another BlueZ/controller interaction.

## 4. Established troubleshooting procedure

If Joystick 3 later fails again:

```text
1. Work from /home/robot/robohub/WSDL/kiro
2. Store BLE joystick evidence under logs/BLE/joystick/
3. Verify hci0 is UP/RUNNING
4. Confirm controller identity: 48:18:8D:52:67:63
5. Use bluetoothctl -m --timeout ... scan on for capturable discovery
6. Inspect bluetoothctl info for Paired / Bonded / Trusted / Connected
7. Attempt direct connection and save the exact BlueZ result
8. If br-connection-create-socket reproduces with valid-looking stored state,
   remove the controller record
9. Put Joystick 3 into PS + SHARE rapid-flash mode
10. Run sudo ds4drv-pair
11. Verify controller operation
12. Verify ROS/teleoperation separately when that layer is under test
```

> [!CAUTION]
> Do **not** use remove/re-pair as the first blind step. Preserve the failure evidence first. The 2026-10-02 recurrence showed why: the initial assumption that the controller had been erased was disproved by discovery and `bluetoothctl info`.

### Logging convention

Use timestamped filenames for repeated evidence so earlier attempts are not overwritten:

```bash
... | tee "logs/BLE/joystick/<description>_$(date +%Y%m%d_%H%M%S).log"
```

## Current state

| Layer | State |
|---|---|
| Husky power | ✅ Working |
| Laptop ↔ Husky communication | ✅ Working |
| SSH as `robot` | ✅ Working |
| Bluetooth adapter `hci0` | ✅ `UP / RUNNING` |
| Joystick 3 identity | ✅ `48:18:8D:52:67:63` |
| 2026-10-02 failure signature | ✅ Reproduced and logged |
| Stale/unusable stored bond | ✅ Reset after evidence capture |
| Fresh pairing | ✅ Recovery operator-confirmed |
| Controller Bluetooth operation | ✅ Working again |
| ROS joystick topic | ⏳ Not asserted by this incident |
| Husky ROS teleoperation | ⏳ Not asserted by this incident |

> [!IMPORTANT]
> **Next investigation boundary:** Bluetooth recovery is complete. Any ROS joystick/topic or Husky teleoperation validation should be recorded as its own directly observed layer rather than inferred from successful Bluetooth pairing.
