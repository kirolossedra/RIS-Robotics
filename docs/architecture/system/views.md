# Whole-System UML Views

**Document role:** structural and behavioral UML-style views of RIS-Robotics, rendered in Mermaid so they remain reviewable directly in the repository.  
**Important:** conceptual elements marked design-only or TBD are architecture elements, not claims that matching code classes already exist.

## Contents

- [Purpose](#purpose)
- [Notation and maturity](#notation-and-maturity)
- [Whole-system structural model](#whole-system-structural-model)
- [Implemented software structure](#implemented-software-structure)
- [Deployment model](#deployment-model)
- [Nominal obstacle sequence](#nominal-obstacle-sequence)
- [Nominal clear sequence](#nominal-clear-sequence)
- [DSP startup and serial-enablement sequence](#dsp-startup-and-serial-enablement-sequence)
- [Transceiver runtime role-switch sequence](#transceiver-runtime-role-switch-sequence)
- [Failure sequence — serial write failure](#failure-sequence--serial-write-failure)
- [Future failure sequence — SSH loss](#future-failure-sequence--ssh-loss)
- [Transceiver runtime state model](#transceiver-runtime-state-model)
- [System semantic state model](#system-semantic-state-model)
- [Target Controlled Robot control activity model](#target-controlled-robot-control-activity-model)
- [UML interpretation notes](#uml-interpretation-notes)

## Purpose

No single UML diagram can faithfully represent a distributed cyber-physical system. This document therefore uses several complementary views:

- structural relationships;
- implemented software object relationships;
- physical deployment;
- nominal runtime sequences;
- failure sequences;
- state machines;
- target control activity.

Together they describe the entire system without pretending that design-only Controlled Robot components are already implemented.

## Notation and maturity

| Diagram element suffix | Meaning |
|---|---|
| `_IMPLEMENTED` | Corresponding repository implementation exists. |
| `_DESIGN_ONLY` | Accepted target element with no repository implementation. |
| `_TBD` | Required concept whose mechanism/value is not selected. |

Where an exact repository class exists, the UML uses its real name. Conceptual future blocks use descriptive architecture names rather than fabricated source-code class names.

## Whole-system structural model

### UML view 1 — conceptual classes/components

```mermaid
classDiagram
    class DummyRobot {
        +provideMovingTarget()
    }
    class RadarRISSystem {
        +observeScene()
        +produceRadarFrames()
    }
    class CentralLaptop {
        +acquireFrames()
        +deriveSemanticState()
        +emitSerialState()
    }
    class TransceiverTX_IMPLEMENTED {
        +acceptOBSCLR()
        +latchState()
        +advertiseState()
    }
    class BLETransport_IMPLEMENTED {
        +protocolVersion 1
        +state CLR_OBS
        +phy CodedS8_or_1M
    }
    class TransceiverRX_IMPLEMENTED {
        +filterPacket()
        +deduplicateState()
        +emitTransition()
    }
    class Controlled RobotSideBridge_DESIGN_ONLY {
        +consumeRXSerial()
        +maintainPersistentSSH()
        +resynchronizeState()
    }
    class Controlled RobotROSArbiter_DESIGN_ONLY {
        +acceptTeleopCommand()
        +acceptSafetyState()
        +applyStopPrecedence()
    }
    class DistanceSource_TBD {
        +distanceToCorner
        +validity
        +age
    }
    class ControlledRobot {
        +executeVelocityCommand()
        +physicalEmergencyStop()
    }
    class HumanOperator {
        +teleoperate()
        +superviseExperiment()
        +useEmergencyStop()
    }

    DummyRobot --> RadarRISSystem : creates observed motion
    RadarRISSystem --> CentralLaptop : sensing data
    CentralLaptop --> TransceiverTX_IMPLEMENTED : OBS / CLR serial
    TransceiverTX_IMPLEMENTED --> BLETransport_IMPLEMENTED : advertise state
    BLETransport_IMPLEMENTED --> TransceiverRX_IMPLEMENTED : receive state
    TransceiverRX_IMPLEMENTED --> Controlled RobotSideBridge_DESIGN_ONLY : OBS / CLR serial
    Controlled RobotSideBridge_DESIGN_ONLY --> Controlled RobotROSArbiter_DESIGN_ONLY : SSH-delivered safety state
    DistanceSource_TBD --> Controlled RobotROSArbiter_DESIGN_ONLY : gating context
    HumanOperator --> Controlled RobotROSArbiter_DESIGN_ONLY : normal cmd_vel
    Controlled RobotROSArbiter_DESIGN_ONLY --> ControlledRobot : final software command
    HumanOperator --> ControlledRobot : physical safety supervision
```

This is a conceptual system UML view. `Controlled RobotSideBridge_DESIGN_ONLY`, `Controlled RobotROSArbiter_DESIGN_ONLY`, and `DistanceSource_TBD` are architecture elements rather than repository classes.

## Implemented software structure

### UML view 2 — implemented DSP and transport-side software

```mermaid
classDiagram
    class RealtimeRadarClassifier {
        +warm_up()
        +process_frame(frame_data)
        -_make_maps(frame_data)
        -_capon_map(profiles, steering_vector)
        -_prepare_map(data)
        -_predict(input_maps)
        +dopp_avg
        +elevation_segment
        +doppler_segment
    }

    class RecordingLoop {
        +record_frames(...)
        +vote_predictions(predictions)
        +discover_serial_device()
        +main(argv)
    }

    class ObstacleStateAdapter {
        +state
        +fault
        +update(voted_name)
    }

    class SerialStateOutput {
        +last_transmitted
        +last_error
        +sync(state)
        +close()
    }

    class SerialDiscovery {
        +find_nrf_boards()
        +discover_nrf_serial_port()
    }

    class SharedTransceiverFirmware {
        +tx_poll_uart()
        +switch_to_rx()
        +switch_to_tx()
        +switch_phy()
        +parse_ad()
        +transceiver_run()
    }

    class ProtocolHelpers {
        +tx_parse_command()
        +rx_dedup_update()
        +tr_press_role_button()
        +tr_press_phy_button()
    }

    class RXLogger {
        +readSerialEvent()
        +timestampUTC()
        +writeJSONL()
    }

    RecordingLoop --> RealtimeRadarClassifier : process frames
    RecordingLoop --> ObstacleStateAdapter : update voted label
    RecordingLoop --> SerialDiscovery : locate TX console
    RecordingLoop --> SerialStateOutput : synchronize state
    SerialStateOutput --> SharedTransceiverFirmware : OBS / CLR UART
    SharedTransceiverFirmware --> ProtocolHelpers : shared protocol logic
    SharedTransceiverFirmware --> RXLogger : RX UART events
```

`RecordingLoop`, `SerialDiscovery`, `SharedTransceiverFirmware`, `ProtocolHelpers`, and `RXLogger` represent modules/function groups rather than Python/C classes. Exact class names are used where classes actually exist.

## Deployment model

### UML view 3 — deployment

```mermaid
flowchart LR
    subgraph Scene[Physical experiment scene]
        H[Dummy Robot]
        R[Radar / RIS hardware]
        J[Controlled Robot]
    end

    subgraph Central[Central sensing laptop]
        DSP[Python DSP application]
        AD[ObstacleStateAdapter]
        SO[SerialStateOutput]
    end

    subgraph TX[nRF52833 DK A]
        FW1[Shared Transceiver firmware<br/>TX runtime role]
    end

    subgraph Radio[Wireless]
        AIR[BLE extended advertising]
    end

    subgraph RX[nRF52833 DK B]
        FW2[Same Transceiver firmware<br/>RX runtime role]
    end

    subgraph Host[Controlled Robot-side host]
        LOG[rx_logger.py]
        BR[Future serial-to-SSH bridge]
    end

    subgraph Onboard[Controlled Robot onboard computer]
        ROS[Future ROS arbiter]
    end

    H --> R
    R -->|USB / vendor SDK| DSP
    DSP --> AD --> SO
    SO -->|USB UART 115200| FW1
    FW1 --> AIR --> FW2
    FW2 -->|USB UART 115200| LOG
    FW2 -. future control path .-> BR
    BR -. Ethernet + persistent SSH .-> ROS
    ROS -. future local command .-> J
```

## Nominal obstacle sequence

### UML view 4 — obstacle episode

```mermaid
sequenceDiagram
    participant Scene as Physical scene
    participant Radar as Radar/RIS
    participant DSP as DSP + rolling vote
    participant Adapter as ObstacleStateAdapter
    participant Serial as SerialStateOutput
    participant TX as NRF TX
    participant RX as NRF RX
    participant Bridge as Controlled Robot bridge (future)
    participant Arbiter as ROS arbiter (future)
    participant Controlled Robot as Controlled Robot

    Scene->>Radar: Person or robot enters conflicting corridor
    Radar->>DSP: Radar frames
    DSP->>DSP: Feature maps + window inference + vote
    DSP->>Adapter: Stable Person detected / Robot detected
    Adapter->>Adapter: CLEAR -> OBSTACLE
    Adapter->>Serial: synchronize OBSTACLE
    Serial->>TX: OBS newline
    TX->>TX: latch OBS
    TX-->>RX: BLE service data state=OBS
    RX->>RX: validate + deduplicate
    RX->>Bridge: OBS newline
    Note over Bridge,Arbiter: Design-only downstream path
    Bridge->>Arbiter: forward unsafe state over persistent SSH
    Arbiter->>Arbiter: combine unsafe + distance gate
    Arbiter->>Controlled Robot: force STOP when gate is active
```

The sequence is partially executable today. Steps through RX serial are implemented; steps after RX serial are target behavior.

## Nominal clear sequence

### UML view 5 — clear transition

```mermaid
sequenceDiagram
    participant DSP as DSP + rolling vote
    participant Adapter as ObstacleStateAdapter
    participant Serial as SerialStateOutput
    participant TX as NRF TX
    participant RX as NRF RX
    participant Arbiter as ROS arbiter (future)

    DSP->>Adapter: Stable Nothing detected
    Adapter->>Adapter: OBSTACLE -> CLEAR
    Adapter->>Serial: synchronize CLEAR
    Serial->>TX: CLR newline
    TX->>TX: latch CLR
    TX-->>RX: repeated BLE state=CLR
    RX->>RX: first CLR after OBS accepted
    RX-->>Arbiter: CLR via future bridge
    Arbiter->>Arbiter: release STOP eligibility according to local policy
```

An initial clear advertisement is intentionally silent at RX; this sequence describes clearing an established obstacle episode.

## DSP startup and serial-enablement sequence

### UML view 6 — guarded startup

```mermaid
sequenceDiagram
    participant App as collect_data_realtime.main
    participant Discover as serial discovery
    participant Model as classifier configuration
    participant Serial as SerialStateOutput
    participant Radar as Radar device

    App->>Discover: find nRF/J-Link boards
    alt no board or ambiguous boards
        Discover-->>App: no serial device
        App->>App: continue DSP with serial disabled
    else one unambiguous board
        Discover-->>App: serial device
        App->>Model: inspect PLACEHOLDER_MODE
        alt placeholder mode without development override
            App->>App: refuse serial-control run
        else trained model or explicit development override
            App->>Serial: open selected device
            App->>Radar: begin acquisition
        end
    end
```

This is a major architectural safeguard: the application does not silently guess a board and does not silently actuate from placeholder inference.

## Transceiver runtime role-switch sequence

### UML view 7 — TX to RX

```mermaid
sequenceDiagram
    participant User as Operator
    participant Button as Button 2 ISR
    participant Loop as transceiver_run
    participant TX as TX transport
    participant RX as RX transport
    participant LEDs as Role LEDs

    User->>Button: press role button
    Button->>Loop: set role-switch request
    Loop->>TX: stop advertising
    Loop->>Loop: discard partial UART + reset RX epoch
    Loop->>RX: start scanning on current PHY
    alt scan starts
        RX-->>Loop: success
        Loop->>Loop: commit active role RX
        Loop->>LEDs: steady RX role LED; packet LED pulses on receive
    else scan fails
        RX-->>Loop: error
        Loop->>TX: attempt previous TX restore
        alt restore succeeds
            Loop->>LEDs: retain TX role LED and advertising pulses
        else restore fails
            Loop->>LEDs: role LEDs off
        end
    end
```

The active role is committed only after its BLE transport starts successfully. This keeps visual role indication tied to real transport state rather than requested state.

## Failure sequence — serial write failure

### UML view 8 — implemented retry semantics

```mermaid
sequenceDiagram
    participant Adapter as ObstacleStateAdapter
    participant Writer as SerialStateOutput
    participant Port as Serial transport
    participant Loop as DSP recording loop

    Adapter->>Writer: sync(new semantic state)
    Writer->>Port: write OBS or CLR
    Port-->>Writer: write failure
    Writer->>Writer: keep last_transmitted unchanged
    Writer-->>Loop: false + visible last_error
    Loop->>Loop: continue according to current application behavior
    Note over Writer: Next sync sees transport still stale and retries
```

Transport failure does not advance the writer's record of what reached the downstream side.

## Future failure sequence — SSH loss

### UML view 9 — required design behavior, not implemented

```mermaid
sequenceDiagram
    participant RX as NRF RX
    participant Bridge as Future bridge
    participant SSH as SSH session
    participant Arbiter as Future ROS arbiter

    RX->>Bridge: OBS / CLR transition
    Bridge->>SSH: forward state
    SSH--xBridge: connection lost
    Bridge->>Bridge: mark connection unhealthy
    Note over Bridge,Arbiter: Reconnect, authoritative state recovery, and stale-state policy are still TBD
    Bridge-->>Arbiter: must not invent CLR from silence
```

This diagram is intentionally incomplete at the policy point because the repository has not selected the reconnect/fail-safe semantics yet.

## Transceiver runtime state model

### UML view 10 — role and PHY orthogonality

```mermaid
stateDiagram-v2
    [*] --> TX_S8
    TX_S8 --> RX_S8: Button 2 / role switch
    RX_S8 --> TX_S8: Button 2 / role switch
    TX_S8 --> TX_1M: Button 1 / PHY switch
    TX_1M --> TX_S8: Button 1 / PHY switch
    RX_S8 --> RX_1M: Button 1 / PHY switch
    RX_1M --> RX_S8: Button 1 / PHY switch
    TX_1M --> RX_1M: Button 2 / role switch
    RX_1M --> TX_1M: Button 2 / role switch
```

Role and PHY are independent state dimensions. The firmware additionally has failure recovery around transport restart; the simplified state chart above shows only successful active modes.

## System semantic state model

### UML view 11 — semantic and transport state

```mermaid
stateDiagram-v2
    [*] --> CLEAR
    CLEAR --> OBSTACLE: stable person or robot
    OBSTACLE --> CLEAR: stable nothing
    CLEAR --> CLEAR: stable nothing
    OBSTACLE --> OBSTACLE: stable person or robot
    CLEAR --> CLEAR: unknown / invalid / fault
    OBSTACLE --> OBSTACLE: unknown / invalid / fault
```

The semantic FSM is deliberately conservative: unknown/fault holds state. It does not interpret lack of a valid classification as evidence of clearance.

## Target Controlled Robot control activity model

### UML view 12 — future local decision activity

```mermaid
flowchart TD
    START([New control cycle])
    TELEOP[Read normal teleoperation command]
    SAFETY[Read latest safety state]
    VALID{Safety state valid and live?}
    DIST[Read distance-to-corner]
    DVALID{Distance valid and live?}
    UNSAFE{Obstacle state unsafe?}
    NEAR{Distance <= threshold?}
    STOP[Output zero / STOP command]
    PASS[Allow normal cmd_vel]
    POLICY[Apply explicit failure policy<br/>TBD]
    END([Publish final local command])

    START --> TELEOP --> SAFETY --> VALID
    VALID -->|No| POLICY --> END
    VALID -->|Yes| DIST --> DVALID
    DVALID -->|No| POLICY
    DVALID -->|Yes| UNSAFE
    UNSAFE -->|No| PASS --> END
    UNSAFE -->|Yes| NEAR
    NEAR -->|Yes| STOP --> END
    NEAR -->|No| PASS
```

The `POLICY` branch is intentionally unresolved. A professional architecture should show the missing decision explicitly rather than conceal it behind an assumed default.

## UML interpretation notes

- Mermaid `classDiagram` is used for UML-style structure because it renders directly in GitHub; it is not a claim that every conceptual component is implemented as a software class.
- Deployment diagrams are represented with Mermaid subgraphs because native UML deployment rendering is not available directly in GitHub Markdown.
- Sequence diagrams explicitly show where the implemented chain ends and future behavior begins.
- State diagrams model only state dimensions supported by implementation or accepted architecture; no unselected distance/localization mechanism is invented.
- Exact protocol and interface details remain authoritative in [`interfaces.md`](../interactions/interfaces.md), while implementation maturity remains authoritative in [`implementation-status.md`](current-state.md).
