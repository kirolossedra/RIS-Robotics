# DSP Subsystem

## Contents

- [Responsibility](#responsibility)
- [Pipeline](#pipeline)
- [Maturity](#maturity)
- [Implementation detail](#implementation-detail)

## Responsibility

Reduce Radar/RIS observations from raw frames to stable semantic state and then to the transport-neutral `CLEAR` / `OBSTACLE` state.

## Pipeline

```text
acquisition
 -> range/Doppler/MTI/Capon features
 -> 10-frame model window
 -> CNN-LSTM inference
 -> rolling vote
 -> semantic obstacle adapter
 -> transition-oriented OBS/CLR output
```

## Maturity

Acquisition, feature construction, voting, obstacle-state adaptation, and serial integration code exist. The classifier slot is currently **Placeholder + Blocked** for experiment control because the installed model is not the trained person/robot/nothing detector.

## Implementation detail

Detailed algorithms remain under [`../../../dsp/docs/`](../../../dsp/docs/). Those documents are implementation detail, not a parallel whole-system architecture authority.
