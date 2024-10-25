#!/usr/bin/env python3
import os
import sys
import threading
import time

# ROS2 Imports
import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor

from ament_index_python.packages import get_package_share_directory

from dca1000_ros2_pkg.msg import ControlStatus
from dca1000_ros2_pkg.srv import SendDeviceControlCommand

class MMWaveTermCli(Node):

    cmdDICT = {
        "SETUP":2,
        "START":1,
        "STOP":0
    }
    
    radar_status = {
        'PWRON':False, 
        'SETUP':False, 
        'RECRD':False
    }

    def __init__(self):

        super().__init__("radar_client_node") 
        self.get_logger().info("init")
        
        package_name = 'dca1000_ros2_pkg'
        share_directory = get_package_share_directory(package_name)
        dev_cfg_file_path = os.path.join(share_directory, 'config', 'cfgDev.json')

        self.declare_parameter('dev_cfg_file_path', dev_cfg_file_path)
        self.devConfigPath = self.get_parameter('dev_cfg_file_path').get_parameter_value().string_value
        path = self.devConfigPath

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

        self.status_subscription = self.create_subscription(ControlStatus, self.devSPUB, self.status_callback, 10)

        self.cli = self.create_client(SendDeviceControlCommand, self.devSERV)
        self.get_logger().info("created client")

        while not self.cli.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('service not available, waiting again...')
        self.req = SendDeviceControlCommand.Request()
        self.get_logger().info("done init")


    def run(self):

        try:
            time.sleep(2)

            if not self.radar_status['PWRON']:
                self.get_logger().error('Radar is not powered on, please restart.')
                return

            self.get_logger().info("Setting up Radar")
            self.setup_radar()
            start_time = time.time()
            while not self.radar_status["SETUP"]:
                if time.time() - start_time > 10:
                    self.get_logger().error('Radar took too long to start. Please review configs.')
                    return
                time.sleep(0.1)

            self.get_logger().info("Start Publishing")
            self.start_radar()
            start_time = time.time()
            while not self.radar_status["RECRD"]:
                if time.time() - start_time > 10:
                    self.get_logger().error('Radar took too long to start recording.')
                    return
                time.sleep(0.1)
            self.get_logger().info("Radar successfully set up")

            while True:
                time.sleep(10)

        except KeyboardInterrupt:

            self.get_logger().info("Stopping radar")
            self.stop_radar()

    def status_callback(self, msg):

        self.radar_status['PWRON'] = msg.pwron
        self.radar_status['SETUP'] = msg.setup
        self.radar_status['RECRD'] = msg.recrd

    def send_request(self, cmd):
        self.get_logger().info('Sending Request...')
        self.req.command = cmd
        self.future = self.cli.call_async(self.req)
        rclpy.spin_until_future_complete(self, self.future)
        return self.future.result()

    def setup_radar(self):
        response = self.send_request(self.cmdDICT["SETUP"])
        print(response)

    def start_radar(self):
        response = self.send_request(self.cmdDICT["START"])
        print(response)

    def stop_radar(self):
        response = self.send_request(self.cmdDICT["STOP"])
        print(response)

def main(args=None):
    print('client started')

    node = MMWaveTermCli()
    node.run()
    
    print("Shutting Down")
    rclpy.shutdown()


if __name__ == "__main__":
    main()




