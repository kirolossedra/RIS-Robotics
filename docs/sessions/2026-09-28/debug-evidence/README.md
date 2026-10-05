# Debug evidence (Windows / J-Link investigation, 2026-09-28)

Diagnostic artifacts from the Windows/J-Link BSOD investigation and the
nRF52833 bring-up. Moved here from the repository root on 2026-09-28 so
the root stays clean; history in `../MUSE_SESSION_LOG.md` still names
the old root paths.

## Contents

- `091626-15718-01.dmp`, `092826-15921-01.dmp` — preserved Windows kernel
  crash dumps (bugcheck `0xA`; SEGGER drivers loaded, fault unattributed).
  Large binaries: git-ignored, not for GitHub.
- `JLink_Windows_x86_64.exe` — SEGGER J-Link V9.80 installer used for the
  clean reinstall. Large binary: git-ignored, not for GitHub.
- `segger_jlink_reset_report.md` — stack reset report (inventory, crash
  evidence, removal, clean V9.80 install, reconnection plan).
- `segger_inventory_before.json`, `segger_cleanup_log.txt`,
  `segger_install_log.txt` — install/cleanup tool outputs.
- `jlink_passive_enumeration.json`, `jlink_probe_open_test.jlink` —
  enumeration and probe-open test artifacts.
- `segger_inventory.ps1`, `segger_cleanup.ps1`, `segger_install.ps1`,
  `jlink_passive_enumeration.ps1` — diagnostic scripts used during the
  investigation.

## Note

Live validation evidence (boot captures, smoke tests, packet format)
belongs in `../firmware/validation/`, not here.
