class M2S2Device():
    # %---------------------------------------------------------------------------------------------------------
    # Class Parameters
    # %--------------------------------------------------------------------------------------------------------- 
    # device info
    devNAME = None # name of device in upper case
    devSERV = None # name of device ROS2 service
    devSPUB = None # name of device status publisher
    devDPUB = None # name of device data publishder
    devLOGG = None # String Attached to beginning of log message

    # flags
    devFLAGS_ = None

    # command interperter
    cmdDICT = {
        2:"SETUP",
        1:"RECRD",
        0:"RECRD"
    }

    # %---------------------------------------------------------------------------------------------------------
    # Class Functions
    # %---------------------------------------------------------------------------------------------------------
    # Class constructor
    def __init__(self, devNAME):
        """This class outlines the basic naming conventions and variables required to interface with the m2s2
        control node. 

        The class the following members:
        string devNAME which is the name of the device in upper case. The constructor automatically handles the upper case.
        string devSERV which is the name of the device ROS2 service in the form control_devname in lower case.
        string devSPUB which is the name of the device status publisher
        string devDPUB which is the name of the device data publisher
        dict devFLAGS_ which have the format {'PWRON':False, 'SETUP':False, 'RECRD': False} as default
            PWRON should be set to True device service is created in the node
            SETUP should be set to True after successful setup service request is processed
            RECRD should be set to True after successful record start service request is processed
            RECRD and SETUP should be set to false after successful record stop service request is processed
        dict cmdDict is maps the command constants from m2s2_control_interfaces.srv package to the corresponding flag keys in
            devFLAGS_ 

        :param string devNAME: Name of the device i.e. RADAR or XIMEA or AUDIO
        """
        self.devNAME = devNAME.upper()
        self.devSERV = ("control_%s" % devNAME.lower())
        self.devSPUB = ("%s_status" % devNAME.lower())
        self.devDPUB = ("%s_data" % devNAME.lower())
        self.devLOGG = ("%s: " % devNAME.upper())
        

        self.devFLAGS_ = {
            'PWRON':False, 
            'SETUP':False, 
            'RECRD':False
                }
        
