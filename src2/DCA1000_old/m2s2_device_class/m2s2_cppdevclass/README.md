# M2S2 Generic Device Class
## Description
This is a cpp module designed for linux.
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
1. Navigate to m2s2_cppdevclass directory in terminal. This is the root package directory.
2. In terminal run the following commands
    + In terminal run: mkdir build
    + In terminal run: cd build
    + In terminal run: cmake build ..
    + In terminal run: sudo make install
3. The M2S2 Generic Device headers should be installed in your linux system include.
4. Now you should be able to include the module as normal:
    + #include "M2S2Device.hpp"
5. To access class constructor call
    + M2S2Device dev("DEVICENAME");
6. To build a file (i.e. main.cpp) using the M2S2Device.hpp header, in terminal run:
    + g++ main.cpp -lm2s2_cppdevclass -o main
6. To uninstall the headers navigate into the build directory you created and run:
    + sudo xargs rm < install_manifest.txt