# Validation

## Contents

- [Purpose](#purpose)
- [Validation ladder](#validation-ladder)
- [Evidence map](#evidence-map)
- [Stub validation rule](#stub-validation-rule)

## Purpose

This directory synthesizes what has actually been demonstrated. Raw evidence remains with the subsystem that produced it.

## Validation ladder

1. static/build evidence;
2. hardware-free behavior tests;
3. single-device bring-up;
4. link/subsystem hardware test;
5. integrated subsystem test;
6. end-to-end sensing-to-motion test.

## Evidence map

- DSP tests: [`../../dsp/tests/`](../../dsp/tests/)
- DSP validation notes: [`../../dsp/docs/validation-and-performance.md`](../../dsp/docs/validation-and-performance.md)
- firmware hardware records: [`../../firmware/validation/`](../../firmware/validation/)
- robot hardware troubleshooting evidence: [`../../robotics/`](../../robotics/)
- dated debug/session evidence: [`../sessions/`](../sessions/)

The canonical whole-system validation synthesis is [`system-validation.md`](system-validation.md).

## Stub validation rule

A stub may itself be validated. That proves the substitute and the downstream boundary it exercises—not the real producer it replaces. Stub-driven evidence must remain labeled as such.
