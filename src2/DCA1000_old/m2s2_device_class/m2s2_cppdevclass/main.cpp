#include <include/M2S2Device.hpp>
#include <iostream>
#include <string>
#include <cstring>

int main() {

    char name[]= "testdev";
    M2S2Device device(name);
    std::cout<<"Device Name: "<<device.get_devNAME()<<"\n";
    std::cout<<"Control Service Name: "<<device.get_devSERV()<<"\n";
    std::cout<<"Status Publisher Name: "<<device.get_devSPUB()<<"\n";
    std::cout<<"Data Publisher Name: "<<device.get_devDPUB()<<"\n";

    std::cout<<"\n";
    std::cout<<"cmdDICT values: \n";
    for (auto& t : device.get_cmdDICT())
        std::cout << t.first << " " << t.second << "\n";
    
    std::cout<<"\n";
    std::cout<<"devFLAGS_ values: \n";
    for (auto& t : device.get_devFLAGS_())
        std::cout << t.first << " " << t.second << "\n";

    return 0;

    return 0;
    
}

// to build main run: g++ main.cpp -lm2s2_cppdevclass -o main