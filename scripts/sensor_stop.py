#!/usr/bin/env python3
"""
Find the AWR1843's CLI port and stop the sensor, without going through ROS.

    python3 scripts/sensor_stop.py               # probe every /dev/ttyACM*
    python3 scripts/sensor_stop.py --flush       # also flushCfg, ready for SETUP
    python3 scripts/sensor_stop.py --port /dev/ttyACM1

WHY THIS EXISTS

1. The radar keeps chirping until told to stop. Killing the ROS nodes does not
   stop it -- the sensor has no idea the host went away. And radar_ctrl_node has
   `sensorStop` COMMENTED OUT of its SETUP sequence (radar_ctrl_node.py:286), so
   SETUP sends flushCfg first, which the TI CLI refuses while the sensor is
   running. Every response is checked against == "Done", so SETUP fails on its
   first command and cannot recover the state it needs to fix.

2. The AWR1843BOOST presents TWO ACM devices -- the CLI (user UART) and the data
   port -- and USB enumeration order is NOT guaranteed across reboots. The data
   port opens perfectly and answers nothing. radar_config.yaml hardcodes
   /dev/ttyACM0, so after a reboot that swapped them, radar_ctrl_node opens the
   wrong port and reports "Received invalid response. Please restart." That
   message reads like a radar fault; it is a port-numbering fault.

So: probe, do not assume. Baud 921600 matches radar_ctrl_node.py:339.
"""
import argparse
import glob
import sys
import time

try:
    import serial
except ImportError:
    sys.exit("pyserial not installed:  pip3 install pyserial")


def send(ser, cmd, settle=0.3):
    ser.write((cmd + "\n").encode())
    time.sleep(settle)
    reply = ser.read_all().decode(errors="replace").strip()
    print("  %-12s -> %s" % (cmd, reply.replace("\n", " | ") or "(no reply)"))
    return reply


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default=None, help="default: probe every /dev/ttyACM*")
    ap.add_argument("--baud", type=int, default=921600)
    ap.add_argument("--flush", action="store_true",
                    help="also send flushCfg, leaving the radar ready for a fresh SETUP")
    args = ap.parse_args()

    ports = [args.port] if args.port else sorted(glob.glob("/dev/ttyACM*"))
    if not ports:
        sys.exit("no /dev/ttyACM* devices -- is the radar powered and plugged in?")
    print("probing: %s" % ", ".join(ports))

    # Sweep baud too. 921600 matches radar_ctrl_node.py:339 and demonstrably
    # worked on 26 Aug, but a board that came back from a reset in a default
    # state can sit at the SDK's stock 115200 instead. Cheap to rule out.
    bauds = [args.baud] + [b for b in (115200, 921600) if b != args.baud]
    ser = None
    reply = ""
    for port in ports:
      for baud in bauds:
          try:
              cand = serial.Serial(port, baud, timeout=0.5)
          except Exception as e:
              print("  %-14s cannot open: %s" % (port, e))
              continue
          cand.write(b"\n")                 # clear any half-typed command
          time.sleep(0.05)
          cand.read_all()
          cand.write(b"sensorStop\n")
          time.sleep(0.3)
          probe = cand.read_all().decode(errors="replace").strip()
          if probe:
              print("  %-14s @%d ANSWERS -> %s" % (port, baud, probe.splitlines()[0]))
              ser, reply = cand, probe
              break
          print("  %-14s @%d silent" % (port, baud))
          cand.close()
      if ser is not None:
          break

    if ser is None:
        sys.exit("No ACM port answered the CLI.\n"
                 "  Either a driver process still holds it, or the radar is wedged --\n"
                 "  press NRST on the AWR1843BOOST, or power-cycle it, then retry.")

    if args.flush:
        send(ser, "flushCfg")
    cli_port = ser.port
    ser.close()

    # "Done", "already stopped" and "not been started" all mean the same thing
    # for our purposes: the sensor is not chirping.
    ok = any(k in reply for k in ("Done", "already", "not been started"))
    print("\nCLI port is %s" % cli_port)
    if cli_port != "/dev/ttyACM0":
        print("NOTE: radar_config.yaml hardcodes ser_addr: '/dev/ttyACM0'.")
        print("      Set it to '%s' or SETUP will keep failing with" % cli_port)
        print("      'Received invalid response. Please restart.'")
    print("sensor stopped" if ok else "UNEXPECTED reply -- power-cycle the radar")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
