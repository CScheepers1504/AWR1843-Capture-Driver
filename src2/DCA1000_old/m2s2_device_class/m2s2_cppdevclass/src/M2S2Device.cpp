#include "../include/M2S2Device.hpp"
#include <string>
#include <cstring>
#include <map>
#include <cstdint>

M2S2Device::M2S2Device(char *devNAME_){
    // Convert to uppercase
    for (int x=0; x<strlen(devNAME_); x++)
        devNAME_[x] = (toupper(devNAME_[x]));
    devNAME = std::string(devNAME_);
    // devLOGG = std::string(devNAME_)+": ";

    //Convert to lowercase
    for (int x=0; x<strlen(devNAME_); x++)
        devNAME_[x] = (tolower(devNAME_[x]));
    devSERV = "control_" + std::string(devNAME_);
    devSPUB = std::string(devNAME_)+"_status";
    devDPUB = std::string(devNAME_)+"_data";

    //flags
    devFLAGS_ = {{"PWRON", false}, {"SETUP", false}, {"RECRD", false}};

    //cmdDICT
    cmdDICT = {{0, "RECRD"}, {1, "RECRD"},{2, "SETUP"}};   
}

std::map<std::string, bool> M2S2Device::get_devFLAGS_()
{
    return devFLAGS_;
}

std::map<int8_t, std::string> M2S2Device::get_cmdDICT()
{
    return cmdDICT;
}

std::string M2S2Device::get_devNAME()
{
    return devNAME;
}

std::string M2S2Device::get_devSERV()
{
    return devSERV;
}

std::string M2S2Device::get_devSPUB()
{
    return devSPUB;
}

std::string M2S2Device::get_devDPUB()
{
    return devDPUB;
}

// std::string M2S2Device::get_LOGG()
// {
//     return devLOGG;
// }


