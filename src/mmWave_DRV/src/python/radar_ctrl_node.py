#! /usr/bin/env python3
# Standard Python Imports
import socket
import struct 
import time
import serial
import os
import json

# M2S2 imports
# from m2s2_pydevclass.m2s2_device import M2S2Device

# Package Submodules
# from .submodules.mmwave_config_class import mmWaveConfig
from mmwave_config_class import mmWaveConfig
# import mmwave_config_class

# ROS2 Imports
import rclpy
from rclpy.node import Node
from rclpy.executors import MultiThreadedExecutor
from rclpy.callback_groups import MutuallyExclusiveCallbackGroup, ReentrantCallbackGroup

from ament_index_python.packages import get_package_share_directory

from mmwave_drv.msg import ControlStatus
from mmwave_drv.srv import SendDeviceControlCommand


class MMWaveControlNode(Node):
    # %---------------------------------------------------------------------------------------------------------
    # Class Parameters
    # %---------------------------------------------------------------------------------------------------------

    devFLAGS_ = {
        'PWRON':False, 
        'SETUP':False, 
        'RECRD':False
    }
    
    # useful commands
    dev_cpt_cmd = [ 
        'sensorStop\n',
        'sensorStart\n',
        'flushCfg\n'
        ] 

    dca_cfg_cmd = { 
        'RESET_FPGA_CMD_CODE'               : b"\x5a\xa5\x01\x00\x00\x00\xaa\xee", 
        'CONFIG_FPGA_GEN_CMD_CODE'          : b"\x5a\xa5\x03\x00\x06\x00\x01\x02\x01\x02\x03\x1e\xaa\xee", 
        'CONFIG_PACKET_DATA_CMD_CODE'       : b"\x5a\xa5\x0b\x00\x06\x00\xbe\x05\x35\x0c\x00\x00\xaa\xee", 
        'SYSTEM_CONNECT_CMD_CODE'           : b"\x5a\xa5\x09\x00\x00\x00\xaa\xee", 
        'RECORD_START_CMD_CODE'             : b"\x5a\xa5\x05\x00\x00\x00\xaa\xee", 
        'SYSTEM_ERROR_CMD_CODE'             : b"\x5a\xa5\x0a\x00\x01\x00\xaa\xee", 
        'RECORD_STOP_CMD_CODE'              : b"\x5a\xa5\x06\x00\x00\x00\xaa\xee", 
        }   
        # commands sent over ethernet based on CLI. Consists of header, data size, command code, footer
        # commands above are listed in order of send and receive
        # some commands in the DCA1000 user guide are not used and are thus not included
 
    # Sockets and Ports
    dca_cmd_addr = ('192.168.33.180',4096)      # address to send commands to
    dca_rcv_addr = ('192.168.33.30', 4096)      # address to receive command responses from
    ser_cmd_addr = ('137.158.125.136', 8080)    # address of the serial server device
    dca_socket = None                           # socket variable for the command port

    # configs
    # runDict = None # runtime parameter dictionary 
    devDict = None # device parameter dictionary

    # flags
    errDCA_ = None  # True -> error configuring DCA1000
    cfgDCA_ = None  # True -> DCA successfully configured
    errDEV_ = None  # True -> error configuring Device
    cfgDEV_ = None  # True -> Radar device successfully configured
      

    # %---------------------------------------------------------------------------------------------------------
    # Class Functions
    # %---------------------------------------------------------------------------------------------------------
    # Class constructor
    def __init__(self):

        ## Start Node
        # self.device = M2S2Device("RADAR")
        super().__init__("radar_node") 
        self.get_logger().info("init")

        ## Setup Radar System Components -----------------------------------------------------------------------
        # set flags to defualt
        self.errDCA_ = False
        self.cfgDCA_ = False
        self.errDEV_ = False
        self.cfgDEV_ = False

        package_name = 'mmwave_drv'
        share_directory = get_package_share_directory(package_name)
        dev_cfg_file_path = os.path.join(share_directory, 'config', 'cfgDev.json')

        self.declare_parameter('dev_cfg_file_path', dev_cfg_file_path)

        self.declare_parameter('devNAME', 'radar')
        self.declare_parameter('devSERV', 'control_radar')
        self.declare_parameter('devSPUB', 'radar_status')
        self.declare_parameter('devDPUB', 'radar_data')
        self.declare_parameter('devLOGG', 'radar: ')

        self.declare_parameter('device_type', 'AWR1843')
        self.declare_parameter('ser_addr', '/dev/ttyACM0')

        self.devConfigPath = self.get_parameter('dev_cfg_file_path').get_parameter_value().string_value

        self.devNAME = self.get_parameter('devNAME').get_parameter_value().string_value
        self.devSERV = self.get_parameter('devSERV').get_parameter_value().string_value
        self.devSPUB = self.get_parameter('devSPUB').get_parameter_value().string_value
        self.devDPUB = self.get_parameter('devDPUB').get_parameter_value().string_value
        self.devLOGG = self.get_parameter('devLOGG').get_parameter_value().string_value

        self.device_type = self.get_parameter('device_type').get_parameter_value().string_value
        self.ser_addr = self.get_parameter('ser_addr').get_parameter_value().string_value

        # create socket for command port (all radar commands and responses sent and collected here)
        try:
            self.dca_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.dca_socket.bind(self.dca_rcv_addr)
            self.dca_socket.settimeout(1)
            self.get_logger().info("DCA1000 Command Socket Created Successfully") 
        except Exception as e:
            self.errDCA_ = True
            self.get_logger().info("DCA1000 Command Socket Creation Failed With Exception: %s" % (str(e)))


        ## Setup ROS2 Components -------------------------------------------------------------------------------
        # create callback groups
        self.cllgrpTIMER = MutuallyExclusiveCallbackGroup()
        self.cllgrpSERVR = MutuallyExclusiveCallbackGroup()

        # create timer and client
        self.pubTIMER = self.create_timer(1,self.publish_Status,self.cllgrpTIMER)
        self.staPBLSH = self.create_publisher(ControlStatus,self.devSPUB,10)

        # create radar control service
        self.radSERVR = self.create_service(SendDeviceControlCommand, 
                                            self.devSERV, 
                                            self.radar_Service)
                                            #callback_group=self.cllgrpSERVER)

        # finish node init
        self.get_logger().info("%s Control Node Started" % self.devNAME)
        self.devFLAGS_['PWRON'] = True

        err_code_path = os.path.join(share_directory, 'config', 'error_codes.json')
        with open(err_code_path, 'r') as json_file:
            self.dev_err_codes = json.load(json_file)
                  
    # Primary Functions
    # %---------------------------------------------------------------------------------------------------------
    def radar_Service(self, request, response):
        """Provides interaction with node from main user control node. Request can be SETUP, START or STOP.  
    For setup -> Configures DCA1000 over ethernet and then configures the radar via ROS2 service.
    For start -> First sends the record start command over ethernet to tell the DCA1000 to start monitoring LVDS lanes.
    For stop  -> First sends the sensorStop command over serial to tell the radar to stop transmitting.
    
    :param int toggle: toggle is either a 1 or 0. 1 starts recording and 0 stops recording
    :raises AnyError: raises error and exits program execution if error response was received from startSensor or startRecord command
    """
        ## Configure Radar System --------------------------------------------------------------------------------
        if (request.command == request.SETUP):
            self.cfgDEV_ = False
            self.cfgDCA_ = False
            self.get_logger().info("Received SETUP Request from Client.")
            if not self.devFLAGS_["RECRD"]:
                self.setup_DCA1000()
                self.setup_RADAR() 
            else:
                self.get_logger().info("Device is running. Stop device before attempting config.\n")

            self.devFLAGS_["SETUP"] = self.cfgDCA_ and self.cfgDEV_
            self.display_Status()
            response.status = (self.devFLAGS_["SETUP"])
            return response
        else:

            if (request.command == request.START):
                self.get_logger().info("Received START Request from Client.")
                self.dca_socket.sendto(self.dca_cfg_cmd['RECORD_START_CMD_CODE'], self.dca_cmd_addr)
                self.response_DCA1000('RECORD_START_CMD_CODE')

                if self.send_Request(self.dev_cpt_cmd[request.START]):

                    self.devFLAGS_["RECRD"] = True
                    self.get_logger().info("Radar has started recording. Waiting for stop command.\n")
                    self.display_Status()
                    response.status = self.devFLAGS_["RECRD"]
                    return response
                else:

                    self.get_logger().error("Error setting up recording. Please restart the system")
                    self.errDEV_ = True

            elif (request.command == request.STOP):     
                self.get_logger().info("Received STOP Request from Client.")   

                if self.send_Request(self.dev_cpt_cmd[request.STOP]):

                    self.dca_socket.sendto(self.dca_cfg_cmd['RECORD_STOP_CMD_CODE'], self.dca_cmd_addr)
                    self.response_DCA1000('RECORD_STOP_CMD_CODE')
                    self.devFLAGS_["RECRD"] = False
                    self.get_logger().info("Radar has stopped recording. Ready for next record session.\n")

                else:

                    self.errDEV_ = True
            
            self.display_Status()
            response.status = (not self.errDEV_) and (not self.errDCA_)
            return response

    def publish_Status(self):
        msg = ControlStatus()
        msg.dev_name = self.devNAME             # device name
        msg.pwron = self.devFLAGS_["PWRON"]     # device node is running 
        msg.setup = self.devFLAGS_["SETUP"]     # device is setup
        msg.recrd = self.devFLAGS_["RECRD"]     # device is recording and publishing
        self.staPBLSH.publish(msg)
        #self.display_Status()

    def display_Status(self):
        self.get_logger().info("%s Status: PWRON: %s, SETUP: %s, RECRD %s.\n" %
                                    (self.devNAME,              
                                    self.devFLAGS_["PWRON"],      
                                    self.devFLAGS_["SETUP"],     
                                    self.devFLAGS_["RECRD"]))


    # Helper Functions
    # %---------------------------------------------------------------------------------------------------------    
    def setup_DCA1000(self):
        """Performs setup of DCA1000 over etherent. 
    Sends commands over etherent to command port of DCA1000. Commands
    are listed in dictionary at start of class definition. 
    Function Can cause program to hang on waiting for successful acknowledge of 
    command from DCA1000. 
    :raises AnyError: raises errors if setup commands failed
    """
        if self.errDCA_:
            self.get_logger().error("DCA1000 setup failed: Socket not open.")
            return

        # Set up DCA
        self.get_logger().info("Starting DCA1000 Setup.\n")

        # Setup Command List (Ordered List)
        cfgCmdList = [
            'RESET_FPGA_CMD_CODE',
            'CONFIG_FPGA_GEN_CMD_CODE',
            'CONFIG_PACKET_DATA_CMD_CODE',
            'SYSTEM_CONNECT_CMD_CODE'
            ]

        for cmd in cfgCmdList:
            self.dca_socket.sendto(self.dca_cfg_cmd[cmd], self.dca_cmd_addr)
            self.response_DCA1000(cmd)

        if self.errDCA_:
            self.get_logger().error("DCA1000 setup failed: One or more config commands failed.")
        else:
            self.cfgDCA_ = True

    def setup_RADAR(self):
        """Performs setup of radar using a ROS2 service. 
    This ROS node was developed for use with the Nvidia Jetson Orin. The Orin has a driver
    issue that prevents usb communications with the radar. As such the Orin needs to send the
    commands to another computer of network using tcp protocol. This function calls a ROS2
    TCP service to send strings to the external computer (server).
    :raises AnyError: raises errors if setup commands failed
    """


        cmd_arr = self.get_cmd_arr(self.devConfigPath)

        # empty string to remove initial mmwave prompt
        # cmd_arr.insert(0, '\n')

        cmd_arr.insert(0, 'flushCfg\n')
        # cmd_arr.insert(0, 'sensorStop\n')
        
        if self.send_Request(cmd_arr):
            self.get_logger().info("Radar Device setup succeeded.\n") 
            self.cfgDEV_ = True
        else:
            self.get_logger().error("Radar Device setup failed: One or more config commands failed.")
            
    # %---------------------------------------------------------------------------------------------------------
    def response_DCA1000(self, cmd):
        """ Helper function to listen for given command response from DCA1000. 
        Will wait for command response. Can cause program to hang if acknowledgement packet is missed. 
        Sets the DCA1000 error flag to true if status is 1. 
        :param string cmd: Name of the command sent to DCA1000 and waiting for response. 
        """
        self.get_logger().info("Waiting for " + cmd)

        received = False
        timeoutCount = 0
        status=1
        while (not received) and (timeoutCount<=5):
            try:
                msg, server = self.dca_socket.recvfrom(2048)
                (status,) = struct.unpack('<H', msg[4:6])
                received = True
            except Exception as e:
                self.get_logger().error(cmd + " Failed With Exception: " + str(e))
                timeoutCount += 1
                continue

        if status == 0:
            self.get_logger().info(cmd + " was successful.\n")
        else:
            self.get_logger().error(cmd + " was unsuccessful.")
            self.get_logger().error("Received Following Status: " + str(status) + "\n")
            self.errDCA_ = True

    def send_Request(self, cmd) ->bool:
        '''
        This function sends a request or array of requests to the radar serial port.
        The requests must be in the TI string format.
        To work properly, both the device_type and ser_addr class variables must be set correctly.
        
        Returns:
            boolean: True if the command succeeded, false if it failed.
        '''

        # turn string into list
        if isinstance(cmd, str):
            cmd = [cmd]

        # open serial port
        try:
            self.ser = serial.Serial(self.ser_addr ,baudrate=921600, timeout=0.25)

        except Exception as e:
            self.get_logger().error("Radar Command Port Connection Failed With Exception: %s" % (str(e)))
            return False
        time.sleep(0.02)

        # send empty command to clear all previous content
        try:
            self.ser.write("\n".encode("utf-8"))
            time.sleep(0.02)
            init_str = self.ser.read_all()

        except Exception as e:
            self.get_logger().error("Connection failed with exception: %s" % (str(e)))  
            self.ser.close()
            return False

        for command in cmd:

            try:
                self.ser.write(command.encode("utf-8"))
                
                echo_raw = self.ser.readline()
                response_raw = self.ser.readline()
                banner_raw = self.ser.readline()

                if (len(echo_raw) == 0) or (len(response_raw) == 0):
                    self.get_logger().error("Received invalid response. Please restart.")
                    self.ser.close()
                    return False
                
                echo = echo_raw.decode('utf-8').strip()
                response = response_raw.decode('utf-8').strip()
                
                self.get_logger().info(echo)
                self.get_logger().info(response)
                # self.get_logger().info(banner_raw.decode('utf-8'))

            except Exception as e:
                self.get_logger().info("Connection failed with exception: %s" % (str(e)))  
                self.ser.close()
                return False

            if response == "Done":
                pass
            else:
                code_num = response.replace("Error ", "")

                if code_num in self.dev_err_codes:
                    self.get_logger().error(self.dev_err_codes[code_num])
                else:
                    self.get_logger().error("unknown error code")

                self.ser.close()
                return False
            
        self.ser.close()
        return True

    def get_cmd_arr(self, dev_cfg_path: str):
        '''
        reads in dev and run configs, returns array of command strings.
        '''
        
        if not os.path.exists(dev_cfg_path):
            raise FileNotFoundError("dev config file not found")
        
        cmd_list = []

        config = mmWaveConfig(self.device_type, dev_cfg_path)

        if config.mmwaveParamDict == None:
            raise ValueError("Invalid dev config")

        for cmd_key in list(config.mmwaveParamDict.keys()):
            
            cmd_list.append(config.get_mmWaveCommandString(cmd_key))

        return cmd_list

    # %---------------------------------------------------------------------------------------------------------
    # END OF CLASS
    # %---------------------------------------------------------------------------------------------------------        

def main(args=None):
    rclpy.init()
    node = MMWaveControlNode()
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        node.get_logger().info("Press Ctrl+C to shutdown.\n")
        executor.spin()
        #rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Shutting down.\n")
        # stop radar
        node.send_Request(node.dev_cpt_cmd[0])
        # stop dca
        node.dca_socket.sendto(node.dca_cfg_cmd['RECORD_STOP_CMD_CODE'], node.dca_cmd_addr)
        node.response_DCA1000('RECORD_STOP_CMD_CODE')

        node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
