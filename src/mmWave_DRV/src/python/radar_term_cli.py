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

from mmwave_drv.msg import ControlStatus
from mmwave_drv.srv import SendDeviceControlCommand

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
        
        package_name = 'mmwave_drv'
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

        time.sleep(3)

        self.setup_radar()

        time.sleep(4)

        self.start_radar()

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

    rclpy.init()
    node = MMWaveTermCli()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
        
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down.\n")
        node.destroy_node()
    rclpy.shutdown() 

if __name__ == "__main__":
    main()




