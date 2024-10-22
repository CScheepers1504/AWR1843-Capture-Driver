
#ifndef M2M2_CPPDEVCLASS_HPP
#define M2M2_CPPDEVCLASS_HPP

#include <string>
#include <cstring>
#include <map>
#include <cstdint>

class M2S2Device {
    public:
       /**
        * Creates Instance of an M2S2 Generic Device 
        *
        * This class outlines the basic naming conventions and variables required to interface with the m2s2
        * control node. 
        * 
        * The class the following members:
        * string devNAME which is the name of the device in upper case. The constructor automatically handles the upper case.
        * string devSERV which is the name of the device ROS2 service in the form control_devname in lower case. 
        * string devSPUB which is the name of the device status publisher
        * string devDPUB which is the name of the device data publisher
        * dict devFLAGS_ which have the format {'PWRON':False, 'SETUP':False, 'RECRD': False} as default
        *    PWRON should be set to True device service is created in the node
        *    SETUP should be set to True after successful setup service request is processed
        *    RECRD should be set to True after successful record start service request is processed
        *    RECRD and SETUP should be set to false after successful record stop service request is processed
        * dict cmdDict is maps the command constants from m2s2_control_interfaces.srv package to the corresponding flag keys in
        *    devFLAGS_ 
        *
        * @param devNAME_ Name of the device i.e. RADAR or XIMEA or AUDIO
        */
        M2S2Device(char *devNAME_);

        /**
        * Returns the device flags map (dictionary)
        *
        * @return map of device flags with sctructure {"PWRON": bool, "SETUP": bool, "RECRD": bool}
        */
        std::map<std::string, bool> get_devFLAGS_();

        /**
        * Returns the command map (dictionary)
        * 
        * This mapping relates the integer value from the control service to a string that corresponds to
        * device flag being changed.
        *
        * @return map of device flags with sctructure {0: "RECRD", 1: "RECRD", 2: "SETUP"}
        */
        std::map<int8_t, std::string> get_cmdDICT(); 

        /**
        * Returns the name of the device in upper case
        *
        * @return std::string "DEVICENAME"
        */
        std::string get_devNAME(); 

        /**
        * Returns the name of the device control service in lower case
        *
        * @return std::string "control_devicename"
        */
        std::string get_devSERV(); 

        /**
        * Returns the name of the device status publisher in lower case
        *
        * @return std::string "devicename_status"
        */
        std::string get_devSPUB(); 

        /**
        * Returns the name of the device service in lower case
        *
        * @return std::string "devicename_data"
        */
        std::string get_devDPUB(); 

        /**
        * Returns the string that is at the start of the logger message
        *
        * @return std::string "DEVICENAME:"
        */
        // std::string M2S2Device::get_LOGG();

    private:
        // device info
        std::string devNAME;// name of device
        std::string devSERV; // name of device ROS2 Control service
        std::string devSPUB; // name of device ROS2 Status Publisher
        std::string devDPUB; // name of device ROS2 Data Pubisher
        // std::string devLOGG; // string attached to start of logger message for grep

        //flags
        std::map<std::string, bool> devFLAGS_;

        //cmdDICT
        std::map<int8_t, std::string> cmdDICT;    
};

#endif