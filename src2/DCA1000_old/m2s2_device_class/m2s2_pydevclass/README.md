# M2S2 Generic Device Class
## Description
This class outlines the basic naming conventions and variables required to interface with the m2s2 control node. <br> 
The class the following members:<br>
+ string devNAME which is the name of the device in upper case. The constructor automatically handles the upper case.
+ string devSERV which is the name of the device ROS2 service in the form control_devname in lower case. 
+ dict devFLAGS_ which have the format {'PWRON':False, 'SETUP':False, 'RECRD': False} as default
    + PWRON should be set to True device service is created in the node
    + SETUP should be set to True after successful setup service request is processed
    + RECRD should be set to True after successful record start service request is processed
    + RECRD and SETUP should be set to false after successful record stop service request is processed
+ dict cmdDict is maps the command constants from m2s2_control_interfaces.srv package to the corresponding flag keys in devFLAGS_


## Install instructions
Follow these instructions to install the module.
1. Navigate to m2s2_pydevclass/ directory that contains setup.py in terminal. This is the root package directory.
2. Run "pip install ." 
3. Now should be able to import module as normal:
    + from m2s2_pydevclass.m2s2_device import M2S2Device
4. To access class constructor call
    + device = M2S2Device("DEVICENAME")
5. To uninstall m2s2-pydevclass run:
    + pip uninstall m2s2-pydevclass
6. To upgrade m2s2-pydevclass after making changes:
    + Navigate to m2s2_pydevclass/ directory that contains setup.py
    + In terminal run: pip install --upgrade .
