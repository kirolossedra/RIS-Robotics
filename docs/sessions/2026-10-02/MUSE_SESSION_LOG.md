# MUSE Session Log — 2026-10-02

## Table of contents

- [Husky 1 bring-up and Joystick 3 Bluetooth recurrence](#husky-1-bring-up-and-joystick-3-bluetooth-recurrence)

## Husky 1 bring-up and Joystick 3 Bluetooth recurrence

### Context

During work with **Husky 1** and **Joystick 3** on 2026-10-02, the robot was brought up again for manual-control preparation.

Joystick 3 is the PS4 / DualShock 4 controller previously documented as **Husky 3**, Bluetooth MAC `48:18:8D:52:67:63`.

### Initial robot state

- Husky 1 power was connected.
- Laptop-to-Husky communication worked.
- SSH access to the robot worked.
- The mounting plate had been mounted back onto the Husky.
- The Bluetooth-controller problem recurred for Joystick 3.
- The robot-side project source-of-truth working directory was confirmed as:

```text
/home/robot/robohub/WSDL/kiro
```

- BLE joystick diagnostic evidence is to be stored under:

```text
/home/robot/robohub/WSDL/kiro/logs/BLE/joystick/
```

This path convention was also added to the accepted Husky troubleshooting decision.

### 1. First fresh-pair attempt failed to discover the controller

Joystick 3 was placed in PS4 Bluetooth pairing mode by holding **PS + SHARE** until the light bar rapidly flashed.

The first pairing attempt was:

```bash
sudo ds4drv-pair
```

Observed result:

```text
** This script must be run as sudo **
Searching for PS4 Controller...
No Controller Found
```

The command had been invoked with `sudo`; the relevant result was `No Controller Found`.

### 2. Husky Bluetooth adapter verified healthy

The adapter was checked with:

```bash
hciconfig
```

Observed state:

```text
hci0: Type: Primary  Bus: USB
BD Address: CC:D9:AC:3C:9E:24
UP RUNNING PSCAN
RX errors: 0
TX errors: 0
```

Conclusion: the Husky Bluetooth adapter was present and operational. The investigation remained at discovery / stored controller state rather than adapter availability.

### 3. Logging workflow corrected

A log directory was created under the canonical project tree:

```bash
mkdir -p logs/BLE/joystick
```

An initial non-interactive scan was attempted with:

```bash
timeout 15s bluetoothctl scan on | tee logs/BLE/joystick/joystick3_scan_2026-10-02.log
```

That command produced only:

```text
SetDiscoveryFilter success
```

Inspection with `cat` confirmed the log contained no discovery events. This attempt was therefore retained as a failed logging approach rather than interpreted as evidence that no Bluetooth devices were present.

The working scan form used bluetoothctl monitor mode:

```bash
bluetoothctl -m --timeout 15 scan on | tee logs/BLE/joystick/baseline_scan_2026-10-02.log
```

With Joystick 3 off, this produced live discovery events for many nearby Bluetooth devices, proving the Husky was actively scanning and that the console/file capture path worked.

For subsequent Joystick 3 scans, log names were made non-destructive with timestamps:

```bash
bluetoothctl -m --timeout 15 scan on | tee "logs/BLE/joystick/joystick3_scan_$(date +%Y%m%d_%H%M%S).log"
```

### 4. Joystick 3 positively rediscovered

Joystick 3 was put back into rapid-flash pairing mode and the timestamped monitor scan was run.

The scan reported the known controller MAC:

```text
[CHG] Device 48:18:8D:52:67:63 RSSI: -62
```

This established that:

- the Husky could see Joystick 3 over Bluetooth;
- the controller identity still matched the documented MAC;
- the problem was not simple radio invisibility;
- BlueZ already knew the device well enough to emit a change event rather than only an unknown-device discovery event.

### 5. Stored BlueZ state inspected

The controller record was checked with:

```bash
bluetoothctl info 48:18:8D:52:67:63
```

Observed state:

```text
Device 48:18:8D:52:67:63 (public)
Name: Wireless Controller
Alias: Wireless Controller
Class: 0x00002508 (9480)
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

This disproved the working suspicion that the controller had simply been erased from the Husky. The stored record still existed and looked healthy at the BlueZ metadata level.

### 6. Previous TS-002 failure reproduced exactly

Before deleting any pairing state, a direct reconnect was attempted and logged:

```bash
bluetoothctl connect 48:18:8D:52:67:63 | tee "logs/BLE/joystick/joystick3_connect_$(date +%Y%m%d_%H%M%S).log"
```

Observed result:

```text
Attempting to connect to 48:18:8D:52:67:63
[CHG] Device 48:18:8D:52:67:63 Connected: yes
Failed to connect: org.bluez.Error.Failed br-connection-create-socket
```

This is the same central failure signature recorded in TS-002 on 2026-09-17:

```text
Paired / Bonded / Trusted
        -> transient Connected: yes
        -> br-connection-create-socket
        -> unusable connection
```

The recurrence therefore strengthened the operational diagnosis that the stored bond can remain present and valid-looking while becoming unusable for the controller's BR/EDR HID connection.

### 7. Stale bond reset

Because the exact previous failure had now been reproduced, the existing controller record was deliberately removed:

```bash
bluetoothctl remove 48:18:8D:52:67:63 | tee "logs/BLE/joystick/joystick3_remove_$(date +%Y%m%d_%H%M%S).log"
```

The removal was performed as a targeted recovery step only after the stale/unusable-bond pattern had been demonstrated. It was not used as a generic first troubleshooting action.

The exact removal stdout was not pasted into the chat record, so no more specific removal output is asserted here.

### 8. Fresh pairing and recovery

Joystick 3 was again placed into Bluetooth pairing mode with **PS + SHARE** until rapid flashing.

A fresh pairing was then initiated with:

```bash
sudo ds4drv-pair
```

The user subsequently confirmed that **Joystick 3 is working again**.

The final `ds4drv-pair` stdout was not pasted into this session, so this record does **not** claim that a particular `new_link_key`, `ServicesResolved`, or other line was observed today. Those exact lines were captured during the original 2026-09-17 incident, but today's evidence boundary is the successful recovery confirmed by the operator.

### Result

**PASS — Joystick 3 Bluetooth operation recovered.**

The recurrence followed the same observable pre-repair pattern as TS-002:

```text
Joystick 3 visible
        ->
BlueZ record exists
Paired: yes
Bonded: yes
Trusted: yes
Connected: no
        ->
direct connect
        ->
Connected: yes briefly
        ->
br-connection-create-socket
        ->
remove stale/unusable record
        ->
PS + SHARE
        ->
sudo ds4drv-pair
        ->
operator confirms controller working
```

### Evidence and operational lessons

1. **Do not assume the controller was erased merely because `ds4drv-pair` says `No Controller Found`.**
2. Verify `hci0` first.
3. Use a real monitor-mode scan and preserve it under `logs/BLE/joystick/`.
4. Joystick 3 remains identified by MAC `48:18:8D:52:67:63`.
5. A BlueZ state of `Paired: yes`, `Bonded: yes`, and `Trusted: yes` does not prove the bond is usable.
6. Reproduce and capture the connection error before deleting state.
7. If the same `br-connection-create-socket` failure is present, removing the stale record and performing a clean `ds4drv-pair` remains the validated recovery procedure.
8. Timestamp troubleshooting logs so repeated attempts do not overwrite previous evidence.
9. Robot-side project evidence belongs under `/home/robot/robohub/WSDL/kiro`, with BLE joystick logs specifically under `logs/BLE/joystick/`.

### Remaining boundary

Bluetooth/controller recovery is complete for this recurrence. ROS topic behavior and higher-level teleoperation should only be claimed separately when directly verified during the relevant test.
