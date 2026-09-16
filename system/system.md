# RIS Robotics — System Design

**Status:** Initial design draft  
**Date:** 2026-09-15  
**Document role:** Single full-system architecture figure with supporting explanation and discussion of the design decisions that produced it.

## System Design

The experiment connects the existing Radar/RIS sensing setup to a Clearpath Jackal so that a sensing result can directly influence robot motion. The robot is not being used as an autonomous-navigation research platform. It is manually driven, while the Radar/RIS system provides an independent STOP authority when the conflicting corridor is occupied.

The complete system is shown below as one figure.

```mermaid
flowchart LR

    RADAR["RADAR"]
    RIS["RIS"]

    subgraph CENTRAL["CENTRAL SENSING CORE"]
        direction LR
        CL["Central Laptop<br/>Collects Radar + RIS information<br/>Generates safety decision"]
        UTX(["USB"])
        TX["NRF BLE Board<br/>Transmitter"]
        CL --- UTX --- TX
    end

    BLE(["BLE Broadcast"])

    subgraph MOBILE["JACKAL-SIDE COMPUTE CORE"]
        direction LR
        RX["NRF BLE Board<br/>Receiver"]
        URX(["USB"])
        JL["Laptop on Jackal rack<br/>Receives safety state<br/>Runs robot-side control logic"]
        RX --- URX --- JL
    end

    ETH(["Ethernet"])
    JACKAL["Clearpath Jackal Robot"]

    RUSB(["USB"])
    IUSB(["USB"])

    JOY{{"JOYSTICK CONTROL"}}
    STOP{{"STOP BROADCAST CONTROL"}}

    RADAR --- RUSB --- CL
    RIS --- IUSB --- CL

    CL ==> STOP
    STOP ==> TX

    TX -.-> BLE -.-> RX

    RX ==> JL
    JOY ==> JL

    JL --- ETH --- JACKAL
    JL ==> JACKAL
```

The figure uses a fixed convention so that the architecture is readable even for project members who are not robotics specialists.

| Figure element | Meaning |
|---|---|
| Large rectangular block | Physical device or major compute element |
| Small capsule between blocks | Connection technology or interface stack |
| Solid link | Wired physical/data connectivity |
| Dashed directional link | Wireless BLE broadcast |
| Enclosure | Components that belong to the same local operating assembly/core |
| Hexagonal block | Control input or control signal |
| Thick directional arrow | Control influence or authority rather than ordinary connectivity |

The main convention is that whenever two device blocks are connected, the technology used to cross that boundary is written explicitly between them. The architecture therefore shows the actual sequence of interfaces rather than pretending the whole system uses one stack. In this design the path legitimately changes from USB to BLE to USB to Ethernet.

Radar and RIS are peer sensing inputs and are both connected by **USB** to the **Central Laptop**. The Central Laptop is the first common compute point in the robotics integration. It gathers the relevant sensing information and derives the safety decision used by the robot experiment. The robot does not need raw Radar or RIS data; it only needs the resulting safety state.

The Central Laptop connects by **USB** to the sensing-side NRF board. That NRF board is shown inside the **Central Sensing Core** because it remains a locally attached peripheral. The system does not leave that local core until the BLE transmission occurs.

The sensing-side NRF board broadcasts the safety information using **BLE**. A second NRF board receives that broadcast on the robot side. BLE is therefore the remote bridge between the sensing-side core and the Jackal-side compute core.

The receiving NRF board is connected by **USB** to the laptop carried on the Jackal. The Jackal already has a wooden rack/platform that can carry this laptop during testing. The laptop receives the safety state, participates in robot-side control, and can also support experiment data collection and logging.

The Jackal-side laptop connects to the **Clearpath Jackal over Ethernet**. The NRF board does not directly control the Jackal's drive hardware; the laptop remains the compute bridge between the BLE safety information and the robot's normal control interface.

There are two logical control influences on the robot. The **joystick** provides normal operator motion intent. The **STOP broadcast control** originates from the Central Laptop after the Radar/RIS sensing indicates that the conflicting corridor is unsafe. These two control influences are deliberately drawn differently from ordinary device connectivity because they express control authority rather than merely a physical/data link.

The core rule is:

> **STOP authority has higher priority than joystick motion authority.**

If the operator continues requesting motion while the Radar/RIS-derived state indicates that the conflicting corridor is unsafe, the robot-side control layer must prevent the Jackal from proceeding. When the safety state allows motion again, normal joystick control can continue.

Responsibility is intentionally separated across the system. The Radar/RIS side observes the environment and originates the safety decision. BLE carries the compact safety state. The Jackal-side laptop receives that state, combines it with normal joystick intent, and interfaces to the robot. The Jackal itself executes the resulting motion through its existing low-level control system. The design does not require the Jackal to perform SLAM, localization, autonomous route planning, or hidden-corridor perception.

The software STOP mechanism is part of the research integration and does not replace the Jackal's physical emergency-stop hardware or normal supervised procedures when people are involved in testing.

## Discussion of Decisions

The architecture is intentionally simple because the research focus is the Radar/RIS sensing-to-action demonstration rather than autonomous robotics or networking complexity. Two major design choices changed during planning: the communication path moved from Wi-Fi to BLE, and the robot platform moved from Husky to Jackal.

**Wi-Fi to BLE.** The initial concept placed the operator computer, robot computer, and Radar/RIS processing computer on a common Wi-Fi network. Wi-Fi could have carried operator velocity commands, camera/video traffic, Radar/RIS safety messages, telemetry, logs, and supporting ROS/network traffic. That approach was technically workable, but it mixed the tiny safety signal with the rest of the robot's networking and made the integration unnecessarily broad.

The revised design uses **Bluetooth Low Energy with Nordic NRF boards** for the Radar/RIS safety path. The information being sent is only a compact control/safety state, so BLE provides a much narrower and more explicit interface. It decouples the safety trigger from any Wi-Fi used for teleoperation or camera streaming, avoids requiring raw Radar/RIS data to cross to the robot, avoids unnecessary IP/ROS networking complexity for a small state, and allows the sensing-to-robot link to be tested independently. Wi-Fi may still exist for unrelated robot functions, but it is no longer the transport for the Radar/RIS safety decision.

**Husky to Jackal.** The first robot choice was a Clearpath Husky. Husky was technically suitable and familiar because it had already been used extensively during the Rogers project. At that time it had also been easy to borrow because it was already part of the active project context.

The experiment instead moved to a **Clearpath Jackal**. This was not because Jackal provides better sensing or smarter autonomy. Both robots can support the same manually driven robot plus higher-priority safety override. Jackal is preferred because it is a simpler competent actuator for this corridor experiment and reduces unnecessary robotics overhead.

| Tradeoff | Husky | Jackal | Impact on this experiment |
|---|---|---|---|
| Technical suitability | Suitable for teleoperation + safety override | Suitable for teleoperation + safety override | No meaningful difference in the required core function |
| Familiarity | Already used extensively in the Rogers project | Newer platform for this work | Husky has a familiarity advantage |
| Previous access | Easy to borrow under the Rogers project context | Different access process | Husky historically had easier access |
| Current operating plan | Previous convenient arrangement no longer applies in the same way | Use during normal working hours | Jackal is practical without relocating it |
| Office / after-hours use | Previously easier to arrange | Moving it to the office requires extra administrative steps and a professor's signature | Jackal has less relocation flexibility |
| Physical deployment | More platform/overhead than this simple corridor test requires | Easier and simpler for this experiment | Jackal advantage |
| Experiment complexity | More robotics capability than required | Better aligned with the intentionally simple robot role | Jackal keeps the project focused on Radar/RIS, BLE, and the safety interlock |
| Laptop mounting | No specific convenient mount identified in this plan | Existing wooden rack/platform can carry the laptop | Jackal advantage |
| Robot-side architecture | Joystick/cmd_vel + higher-priority safety override | Same | Changing robots does not change the experimental concept |

A practical consequence of choosing Jackal is access. Taking it from its normal operating area into the office requires additional administrative approval, including extra paperwork and a professor's signature. The current plan is therefore to use the Jackal during **typical working hours** in its normally accessible environment rather than make the experiment dependent on moving it to the office.

The Jackal's existing wooden rack is also useful because the data-collection / robot-side laptop can sit directly on the robot while receiving the BLE safety state, participating in the control path, and collecting experimental data. This avoids introducing another mechanical mounting task before the first tests.

Taken together, the decisions keep the system deliberately constrained: **Radar/RIS performs the sensing, BLE carries the small safety decision, the Jackal-side laptop enforces the control relationship, and the Jackal acts as the physical demonstration platform.**