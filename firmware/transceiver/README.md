# Transceiver Firmware

## Contents

- [Purpose](#purpose)
- [Subdirectories](#subdirectories)
- [Local files](#local-files)

## Purpose

This directory is the Zephyr/nRF Connect SDK application for the shared nRF52833 Transceiver image. One binary can operate as TX or RX at runtime; build-time role splitting does not live here.

For build, flash, hardware behavior, validation status, and cross-system links, start at [`../README.md`](../README.md).

## Subdirectories

| Directory | Purpose | What belongs there |
|---|---|---|
| [`src/`](src/) | Firmware implementation | Runtime role/PHY behavior in `main.c` and protocol/state-machine helpers in `protocol.h` |
| [`tests/`](tests/) | Host-side protocol checks | Unit tests for the pure protocol/state-machine helpers, currently `test_protocol.c` |

Both child directories are leaves at present, so recursion terminates there.

## Local files

| File | Role |
|---|---|
| `CMakeLists.txt` | Zephyr application build definition |
| `Kconfig` | Application configuration options such as test/indicator intervals |
| `prj.conf` | Bluetooth, UART, GPIO, and application configuration for the shared image |
