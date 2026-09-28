# SEGGER/J-Link Windows stack reset report

Date: 2026-09-28 (America/Toronto)

## Pre-change inventory

- J-Link V922 (64-bit Windows), version 9.22, installed at `C:\Program Files\SEGGER\JLink_V922`.
- SEGGER Embedded Studio for ARM 5.44, version 5.44, installed at `C:\Program Files\SEGGER\SEGGER Embedded Studio for ARM 5.44` (not removed or modified).
- `JLinkARM.dll`: `C:\Program Files\SEGGER\JLink_V922\JLinkARM.dll`, file/product version 9.22.
- No SEGGER/J-Link entries existed in machine or user PATH.
- SEGGER/J-Link Driver Store packages:
  - `oem17.inf`: `jlink.inf`, Segger, USB, 2018-08-02, version 2.70.8.0, `JLinkx64.sys`.
  - `oem26.inf`: `jlinkcdc.inf`, SEGGER, Ports, 2019-06-06, version 1.34.0.44950, `JLinkCDC.sys`.
  - `oem44.inf`: `jlinkwinusb.inf`, SEGGER Microcontroller GmbH, USBDevice, 2019-06-14, version 3.0.0.0.
- Nordic nRF Command-Line Tools 10.24.2 and `nrfjprog` 10.24.2 external were installed at `C:\Program Files\Nordic Semiconductor\nrf-command-line-tools`.
- nRF Util 8.1.1 was installed at `C:\nordic_tools\nrfutil.exe`.

## Crash evidence preserved

- 2026-09-28 10:40:52: bugcheck 0x0000000A, parameters `(0x42, 0x2, 0x0, 0xfffff803a30eb01f)`, dump `092826-15921-01.dmp`, Report ID `8396eea7-b506-48ec-b47b-9b19db195e1a`.
- 2026-09-16 19:12:19: bugcheck 0x0000000A, parameters `(0x42, 0x2, 0x0, 0xfffff804e845b58f)`, dump `091626-15718-01.dmp`, Report ID `75889947-b815-4f56-8c2c-e9e5e25cdcb3`.
- Both kernel dumps contain loaded-module strings for `jlinkx64.sys` and `JLinkCDC.sys`, as well as Windows USB/WDF modules. This is evidence that the SEGGER drivers were loaded, not by itself proof that either SEGGER module was the faulting instruction. No local Windows debugger was installed to produce a symbolized `!analyze -v` attribution.
- Workspace copies of both original dumps were preserved without modification.

## Removal and clean installation

- The registered J-Link V9.22 uninstaller completed with exit code 0.
- The V9.22 directory and its DLL were removed.
- `oem17.inf`, `oem26.inf`, and `oem44.inf` were each removed from Driver Store with elevated `pnputil`; their orphaned Add/Remove Programs records were then removed after verifying the packages were absent.
- No Nordic, Microsoft, HID, chipset, Bluetooth, or unrelated USB driver was removed.
- Official SEGGER J-Link V9.80 (2026-09-23) Windows x64 installer was downloaded from SEGGER. Authenticode status was Valid and the signer was SEGGER Microcontroller GmbH.
- The same signed installer staged its bundled current Windows driver set using SEGGER's documented `-InstUSBDriver=1` option.
- An unregistered, byte-identical duplicate V9.80 directory produced by the two installation passes was removed, leaving one registered installation.

## Final state

- Installed J-Link: V9.80 (64-bit Windows), version 9.80, `C:\Program Files\SEGGER\JLink`.
- Only `JLinkARM.dll` found on C: is `C:\Program Files\SEGGER\JLink\JLinkARM.dll`, file/product version 9.80, SHA-256 `11485DF977A5F6E7F82187A64BBC3EBD9E24AB8937B3E9F78F989B0B307B6003`.
- Driver Store contains freshly staged package-matched `oem17.inf` 2.70.8.0, `oem26.inf` 1.34.0.44950, and `oem44.inf` 3.0.0.0. These version numbers are the driver payload bundled by current J-Link V9.80.
- No SEGGER/J-Link PATH entry exists; none is required because J-Link discovery uses installed-location registration.
- `nrfjprog --version` reports `JLinkARM.dll version: 9.80`. Because no alternate `JLinkARM.dll` exists, it resolves to `C:\Program Files\SEGGER\JLink\JLinkARM.dll`.
- Nordic's directory contains adapter DLLs named `jlinkarm_nrf*_nrfjprog.dll`, but no bundled `JLinkARM.dll`; those adapter DLLs are Nordic components and were retained.
- nRF Command-Line Tools remains legacy version 10.24.2. nRF Util remains version 8.1.1.
- Nordic config currently has `auto_update_fw=true`; do not invoke `nrfjprog` against the probe during the first enumeration-only test.
- No J-Link/SEGGER hardware was present during final verification.

## First controlled reconnection

1. Reboot Windows once before reconnecting hardware.
2. After login, open Device Manager and Event Viewer, but do not start J-Link Commander, nrfjprog, nRF Util device commands, an IDE, or a debugger.
3. Connect exactly one J-Link/nRF device directly to a motherboard USB port with a known-good short cable, with no USB hub and (for a separate probe) no target attached or powered.
4. Wait two minutes. Verify that only the expected J-Link interfaces enumerate and inspect each interface's Driver tab/provider/version. Confirm there is no new WHEA, Kernel-PnP, USB, or BugCheck event.
5. Disconnect the device. If enumeration alone crashes Windows, preserve the new dump and do not reconnect again; compare its bugcheck address and loaded/faulting module with the two preserved dumps using WinDbg.
