#!/usr/bin/env python3
import sys
import time
import os

from launch import LaunchDescription
from launch import LaunchService
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor

from ament_index_python.packages import get_package_share_directory

from rclpy.node import Node
import rclpy

from dca1000_ros2_pkg.srv import SendDeviceControlCommand

class mmWaveTerminalClient(Node):

    cmdDICT = {
        "SETUP":2,
        "START":1,
        "STOP":0
    }
    def __init__(self):
        super().__init__('terminal_client_node')

        self.declare_parameter('devNAME', 'radar')
        self.declare_parameter('devSERV', 'control_radar')
        self.declare_parameter('devSPUB', 'radar_status')
        self.declare_parameter('devDPUB', 'radar_data')
        self.declare_parameter('devLOGG', 'radar: ')

        self.devNAME = self.get_parameter('devNAME').get_parameter_value().string_value
        self.devSERV = self.get_parameter('devSERV').get_parameter_value().string_value
        self.devSPUB = self.get_parameter('devSPUB').get_parameter_value().string_value
        self.devDPUB = self.get_parameter('devDPUB').get_parameter_value().string_value
        self.devLOGG = self.get_parameter('devLOGG').get_parameter_value().string_value

        self.cli = self.create_client(SendDeviceControlCommand, self.devSERV)
        self.get_logger().info("created client")

        #print("dca1000/" + self.device.devSERV)
        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('service not available, waiting again...')
        self.req = SendDeviceControlCommand.Request()
        self.get_logger().info("done init")

        time.sleep(5)

        while True:
            setup = input("Set up Radar? (y/n)")
            if setup.lower() == 'y':
                self.get_logger().info('Setting up radar')
                self.setup_radar()
                break
            else:
                self.get_logger().info('invalid command')

            time.sleep(5)

        while True:
            setup = input("Start Recording? (y/n)")
            if setup.lower() == 'y':
                self.get_logger().info('Starting Recording')
                self.start_radar()
                break
            else:
                self.get_logger().info('invalid command')

        while True:
            setup = input("Stop Recording? (y/n)")
            if setup.lower() == 'y':
                self.get_logger().info('Stopping Recording')
                self.stop_radar()
                break
            else:
                self.get_logger().info('invalid command')

    def setup_radar(self):
        response = self.send_request(self.cmdDICT["SETUP"])
        print(response)

    def start_radar(self):
        response = self.send_request(self.cmdDICT["START"])
        print(response)

    def stop_radar(self):
        response = self.send_request(self.cmdDICT["STOP"])
        print(response)

    def send_request(self, cmd):
        self.get_logger().info('Sending Request...')
        self.req.command = cmd
        self.future = self.cli.call_async(self.req)
        rclpy.spin_until_future_complete(self, self.future)
        return self.future.result()

def main(args=None):
    # rclpy.init(args=args)
    # mmwave_term_cli = mmWaveTerminalClient()
    # rclpy.spin_once(mmwave_term_cli)

    # mmwave_term_cli.destroy_node()
    # rclpy.shutdown()

    rclpy.init()
    node = mmWaveTerminalClient()
    executor = MultiThreadedExecutor()
    executor.add_node(node)

    ros2ExecThread = threading.Thread(target=executor.spin,daemon=True)
    ros2ExecThread.start()

    print("Shutting Down")
    rclpy.shutdown()
    ros2ExecThread.join()

if __name__ == '__main__':
    main()