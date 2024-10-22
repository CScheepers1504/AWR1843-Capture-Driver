#! /usr/bin/env python3
# Standard Python Imports
import json # or whatever you need

# M2S2 imports
from m2s2_pydevclass.m2s2_device import M2S2Device

# ROS2 Imports
import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup # , ReentrantCallbackGroup # Reentrant is here if needed

# ROS2 Interface Imports
from m2s2_control_interfaces.msg import ControlStatus
from m2s2_control_interfaces.srv import SendDeviceControlCommand

class M2S2DeviceTemplateNode(Node):
    # %---------------------------------------------------------------------------------------------------------
    # Class Parameters
    # %---------------------------------------------------------------------------------------------------------
    # M2S2 Device Specification 
    device = None

    # %---------------------------------------------------------------------------------------------------------
    # Class Functions
    # %---------------------------------------------------------------------------------------------------------
    # Class constructor
    def __init__(self):

        ## Start Node
        self.device = M2S2Device("EXAMPLE")
        super().__init__("%s_node" % self.device.devNAME) 

        ## Setup EXAMPLE System Components -----------------------------------------------------------------------

        ## Setup ROS2 Components -------------------------------------------------------------------------------
        # setup callback groups
        self.cllgrpDPUBLSH = MutuallyExclusiveCallbackGroup()
        self.cllgrpSPUBLSH = MutuallyExclusiveCallbackGroup()
        self.cllgrpSERVER = MutuallyExclusiveCallbackGroup()

        # create publishers
        self.DPUBLSH = self.create_publisher(ExampleDataMsg,self.device.devDPUB, 10, callback_group=self.cllgrpDPUBLSH)
        self.SPUBLSH = self.create_publisher(ControlStatus, self.device.devSPUB, 10, callback_group=self.cllgrpSPUBLSH)

        # create radar control service
        self.service = self.create_service(SendDeviceControlCommand, 
                                            self.device.devSERV, 
                                            self.example_Service, 
                                            callback_group=self.cllgrpSERVER)

        ## Start threads -----------------------------------------------------------------------------------------

        ## Finish Init -------------------------------------------------------------------------------------------
        self.get_logger().info("%s Node Started" % self.device.devNAME)
        self.device.devFLAGS_['PWRON'] = True
        self.publish_Status()

    # Primary Functions
    # %---------------------------------------------------------------------------------------------------------
    def example_Service(self, request, response):
        """Provides interaction with node from main user control node. Request can be SETUP, START or STOP.  
     
    :param int request: request is either a 1/0 for start/stop record. Or is 2 for SETUP
    :param bool response: response returns true if command successful and false otherwise
    
    :return response: response must be returned for service request to be completed
    """
        ## Configure Radar System --------------------------------------------------------------------------------
        if (request.command == request.SETUP):
            self.get_logger().info("Received SETUP from Control Node.")
            if self.device.devFLAGS_["SETUP"]:
                self.get_logger().info("Radar already setup.\n")
            else:
                self.setup_Device()
            response.status = (self.device.devFLAGS_["SETUP"])
        else:
            if (request.command == request.START) and (not self.device.devFLAGS_["RECRD"]):
                self.get_logger().info("Received START from Control Node. Starting record sequence.")
                # DO RECORD THINGS AND SET RECRD FLAG ACCORDINGLY
                response.status = self.device.devFLAGS_["RECRD"]

            elif (request.command == request.STOP) and (self.device.devFLAGS_["RECRD"]):     
                self.get_logger().info("Received STOP from Control Node. Starting stop sequence.")   
                # DO RECORD THINGS AND SET RECRD AND SETUP FLAGS ACCORDINGLY
                # example: want both setup and record to be set to false so must return true only if both are false
                response.status = not (self.device.devFLAGS_["RECRD"] or self.device.devFLAGS_["SETUP"] ) # change as needed
            else:
                response.status = False

            # publish device status for control subscriber
            self.publish_Status()

            # finish device request
            return response

    # Thread Functions
    # %---------------------------------------------------------------------------------------------------------
    # Add any required functions device template does not include function for publishing device data as too varied
    
                
    # Status Publisher Callback
    # %---------------------------------------------------------------------------------------------------------
    def publish_Status(self):
        msg = ControlStatus()
        msg.dev_name = self.device.devNAME
        msg.pwron = self.device.devFLAGS_['PWRON']
        msg.setup = self.device.devFLAGS_['SETUP']
        msg.recrd = self.device.devFLAGS_['RECRD']
        self.SPUBLSH.publish(msg)
        self.get_logger().info('%s Status:> POWER: %s, SETUP: %s, RECORD: %s\n' 
                                    % (self.device.devNAME,
                                    self.excFLAGS_['PWRON'], 
                                    self.excFLAGS_['SETUP'], 
                                    self.excFLAGS_['RECRD']))

    # Helper Functions
    # %---------------------------------------------------------------------------------------------------------    
    def setup_Device(self):
        self.device.devFLAGS_["SETUP"] = True # or false, add functionality as needed

    def start_Record(self):
        self.device.devFLAGS_["RECRD"] = True # or false, add functionality as needed

    def stop_Record(self):
        self.device.devFLAGS_["SETUP"] = False # or false, add functionality as needed
        self.device.devFLAGS_["RECRD"] = False # or false, add functionality as needed
    
    # %---------------------------------------------------------------------------------------------------------
    # END OF CLASS
    # %---------------------------------------------------------------------------------------------------------        

def main(args=None):
    rclpy.init()
    node = M2S2DeviceTemplateNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        node.get_logger().info('Shut down with CTRL-C.\n')
        executor.spin()
    except KeyboardInterrupt:
        node.get_logger().info('Keyboard interrupt, shutting down.\n')
        exit()
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()