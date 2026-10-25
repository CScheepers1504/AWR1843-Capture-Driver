# AWR1843 Capture Driver

The capture driver repository for a TI AWR1843Boost + DCA1000EVM Capture Board.
It records raw ADC frames from a TI AWR1843BOOST through a DCA1000EVM, tested on an NVIDIA Jetson. Checks have been implemented for every capture before it is used.

While it can be used for general use cases, this repository is one of two used for a generalised sports ball launch monitor. If interested, the analysis half, `launchmon`, is in
[FMCW-Radar-Launch-Monitor](https://github.com/CScheepers1504/FMCW-Radar-Launch-Monitor).

The driver utilises a ROS 2 driver in `src/mmWave_DRV`, which was inherited (Haug, University of Cape Town), kept with its
git history, but altered and hardened for this project. Its own README describes the driver as inherited.

## One take

From a laptop, with the Jetson (or whichever computer the AWR1843 is connected to) on the radar subnet:

```
wsl.exe -e bash session.sh <name> "<note>" --frames 2000     # or .\session from PowerShell
wsl.exe -e bash session.sh --reference                       # empty scene, once per rig position
```

`session.sh` deploys, builds and launches the driver on first use, arms the radar, records,
stops, checks the capture and pulls it back. The driver stays up between takes.
`session.sh --help` lists the options.

## What each capture holds

`recorder.py` writes one folder per take:

| File | Contents |
|---|---|
| `frames.bin` | raw int16 frame payloads, concatenated |
| `index.csv` | per frame: sequence number, timestamps, byte offset, DCA1000 stream offset, burst phase |
| `meta.json` | the radar profile, frame dimensions, a capture summary and the two checks below |

The capture summary reports the publisher's own frame count next to the recorder's, so a slow
subscriber cannot pass for a slow radar.

## Checks on every take

| Script | Question | Writes to `meta.json` |
|---|---|---|
| `scripts/chirp_align_check.py` | does the take start on an Rx-block boundary? | `chirp_align` |
| `scripts/tx_order_check.py` | is the Tx slot order the same as the rig's reference? | `tx_order_check` |

A take whose slot order differs from the reference is renamed `*_TXSLIP`.
`scripts/load_capture.py` reads a capture realigned by those two stamps.

## Other tools

| Script | Role |
|---|---|
| `scripts/profile_check.py <config.json>` | derives resolution, LVDS load, migration and ambiguity from a profile and checks its constraints |
| `scripts/sensor_stop.py` | finds the CLI serial port and stops the sensor without ROS |
| `scripts/monitor.sh` | wire rate from `/proc/net/dev`, independent of ROS 2 |
| `deploy.sh` | one-way laptop to Jetson push, refusing empty files and converting CRLF |
| `scripts/run.sh`, `scripts/record.sh` | launch the driver and record by hand |

## Changes to the inherited driver

- `Frame.msg` carries `uint8[]` rather than `byte[]`, which rclpy delivers as one array instead of
  one Python object per byte. The recorder now keeps up with the 333 Hz publisher.
- The publisher uses best-effort QoS and no longer logs every frame.
- The data node stamps each frame with its DCA1000 stream offset and the timed frame start
  (burst phase), and the zero-fill for dropped packets inserts the right number of packets.
- The control node clears its error flags at the start of each command, and the launch file can
  leave the radar to an external controller (`use_client:=false`).
- The scripts find the workspace and profile from the tree rather than hard-coded paths.

Profiles are in `src/mmWave_DRV/config`, and `radar_config.yaml` names the one the driver loads.
The results were recorded with `awr1843_wideband_lowfs.json`.

## Contributors
Chris Scheepers

Radar Remote Sensing Group, University of Cape Town

Sebastian Haug

## Last Updated 
25 October 2026