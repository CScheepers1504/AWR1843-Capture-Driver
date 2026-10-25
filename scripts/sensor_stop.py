#!/usr/bin/env python3
"""
Find the AWR1843's CLI serial port and stop the sensor, without ROS.

    python3 scripts/sensor_stop.py               # probe every /dev/ttyACM*
    python3 scripts/sensor_stop.py --flush       # also flushCfg, ready for SETUP
    python3 scripts/sensor_stop.py --port /dev/ttyACM1

Killing the ROS nodes leaves the sensor chirping, and SETUP cannot recover a running sensor.
The CLI and data ports can swap numbers across reboots, so every port is probed.
"""
import argparse
import glob
import sys
import time

try:
    import serial
except ImportError:
    sys.exit("pyserial not installed:  pip3 install pyserial")


def send(port, cmd, settle=0.3):
    port.write((cmd + "\n").encode())
    time.sleep(settle)
    reply = port.read_all().decode(errors="replace").strip()
    print("  %-12s -> %s" % (cmd, reply.replace("\n", " | ") or "(no reply)"))
    return reply


def find_cli(ports, bauds):
    """First (open serial port, reply) that answers sensorStop, or (None, "")."""
    for name in ports:
        for baud in bauds:
            try:
                candidate = serial.Serial(name, baud, timeout=0.5)
            except Exception as e:
                print("  %-14s cannot open: %s" % (name, e))
                continue
            candidate.write(b"\n")                 # clear any half-typed command
            time.sleep(0.05)
            candidate.read_all()
            candidate.write(b"sensorStop\n")
            time.sleep(0.3)
            reply = candidate.read_all().decode(errors="replace").strip()
            if reply:
                print("  %-14s @%d answers: %s" % (name, baud, reply.splitlines()[0]))
                return candidate, reply
            print("  %-14s @%d silent" % (name, baud))
            candidate.close()
    return None, ""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default=None, help="default: probe every /dev/ttyACM*")
    parser.add_argument("--baud", type=int, default=921600)
    parser.add_argument("--flush", action="store_true",
                        help="also send flushCfg, leaving the radar ready for a fresh SETUP")
    args = parser.parse_args()

    ports = [args.port] if args.port else sorted(glob.glob("/dev/ttyACM*"))
    if not ports:
        sys.exit("No /dev/ttyACM* devices: is the radar powered and plugged in?")
    print("probing: %s" % ", ".join(ports))

    # A board that came back from a reset in its default state can sit at the SDK's 115200.
    bauds = [args.baud] + [b for b in (115200, 921600) if b != args.baud]
    port, reply = find_cli(ports, bauds)
    if port is None:
        sys.exit("No port answered. A driver may still hold it, or the radar is stuck: "
                 "press NRST or power-cycle it, then retry.")

    # "Done", "already stopped" and "not been started" all mean the sensor is not chirping.
    stopped = any(k in reply for k in ("Done", "already", "not been started"))

    # sensorStop can answer with only its echo and the prompt on a sensor that is already
    # stopped. flushCfg settles it, because the CLI refuses it while the sensor is running.
    # It is harmless, since every SETUP begins with flushCfg.
    if args.flush or not stopped:
        if "Done" in send(port, "flushCfg"):
            stopped = True
    cli_port = port.port
    port.close()
    print("\nCLI port is %s" % cli_port)
    if cli_port != "/dev/ttyACM0":
        print("Set ser_addr in radar_config.yaml to %s, or SETUP fails with 'Received invalid response'."
              % cli_port)
    print("sensor stopped" if stopped else "unexpected reply: power-cycle the radar")
    return 0 if stopped else 1


if __name__ == "__main__":
    sys.exit(main())
