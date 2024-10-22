// Standard Includes
#include <functional>
#include <string>
#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <cstring>
#include <sys/socket.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <chrono>
#include <thread>
#include <memory>
#include <iostream>
#include <fstream>
#include <thread>
#include <signal.h>

#include <jsoncpp/json/json.h>

// ROS2 Includes
#include <rclcpp/rclcpp.hpp>
#include <ament_index_cpp/get_package_share_directory.hpp>

   

// Package Includes
#include "dca1000_ros2_pkg/msg/frame.hpp"
#include "dca1000_ros2_pkg/ringbuffer.hpp"

// Namespaces
using namespace std::chrono_literals;

// Defines
#define PORT 4098
#define DCA_IP_ADDR "192.168.33.30"
#define BUFSIZE 1466
#define DEVICE_NAME "RADAR"
#define MAX_PACKET_DATA_SIZE 1456
//#define RECV_BUFFER_DEFAULT_SIZE 65536
#define RECV_BUFFER_DEFAULT_SIZE 536870912 //512mb

class MMWaveDataNode : public rclcpp::Node
{
  public:
    MMWaveDataNode()
    : Node("RADAR_data_node"), count(0)
    {
        // Device Instantiation ----------------------------------------------------------------
        RCLCPP_INFO(this->get_logger(),"RADAR DATA NODE:");
        RCLCPP_INFO(this->get_logger(),"Starting c++ radar data node.\n");
        char name[]= DEVICE_NAME;
        // M2S2Device device(name);

        // Create Socket -----------------------------------------------------------------------
        RCLCPP_INFO(this->get_logger(),"CONNECTION SETUP:");
        {
          RCLCPP_INFO(this->get_logger(),"Creating Socket...");
        sockfd = socket(AF_INET, SOCK_DGRAM, 0);
        if (sockfd < 0) {
          RCLCPP_ERROR(this->get_logger(),"Could not create socket.\n");
        }
        RCLCPP_INFO(this->get_logger(),"Socket created successfully.\n");
        
        { // Set Socket options
          // reuse address is on to prevent address already in use error 
          optval = 1;
          setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, 
	              (const void *)&optval , sizeof(int));

          // set socket timeout to indefinite
          struct timeval tv;
          tv.tv_sec = 2;
          tv.tv_usec = 0;
          setsockopt(sockfd, SOL_SOCKET, SO_RCVTIMEO, 
	              &tv, sizeof(tv));

          // set socket recvbuffer size
          int recvbuf = RECV_BUFFER_DEFAULT_SIZE*3;
          setsockopt(sockfd, SOL_SOCKET, SO_RCVBUF, 
	              &recvbuf, sizeof(recvbuf));
        }
        
        //assign values
        serveraddr.sin_addr.s_addr = inet_addr(DCA_IP_ADDR);
        serveraddr.sin_family = AF_INET;
        serveraddr.sin_port = htons(PORT);

        //checks connection
        RCLCPP_INFO(this->get_logger(),"Connecting to device...");
        if (bind(sockfd, (struct sockaddr *)&serveraddr, sizeof(serveraddr)) < 0) {
          RCLCPP_ERROR(this->get_logger(),"Connection error\n");
        } else {
          RCLCPP_INFO(this->get_logger(),"Connection successful.\n");
        }
        }

        // Read config data ---------------------------------------------------------------------
        RCLCPP_INFO(this->get_logger(),"DEVICE CONFIG:");
        {

          std::string package_name = "dca1000_ros2_pkg";
          std::string share_directory = ament_index_cpp::get_package_share_directory(package_name);
          std::string run_cfg_file_path = share_directory + "/config/cfgRun.json";
          std::string dev_cfg_file_path = share_directory + "/config/cfgDev.json";
      
          // get jsons
          this->declare_parameter("run_cfg_file_path", run_cfg_file_path);
          this->declare_parameter("dev_cfg_file_path", dev_cfg_file_path);

          Json::Reader reader;
          
          std::string devCfgPath =this->get_parameter("dev_cfg_file_path").get_parameter_value().get<std::string>();
          RCLCPP_INFO(this->get_logger(),"getting dev config at %s\n", devCfgPath.c_str());
          std::ifstream dev(devCfgPath);
          Json::Value devCfgData;
          reader.parse(dev, devCfgData);

           
          std::string runCfgPath =this->get_parameter("run_cfg_file_path").get_parameter_value().get<std::string>();
          RCLCPP_INFO(this->get_logger(),"getting run config at %s\n", runCfgPath.c_str());
          std::ifstream run(runCfgPath);
          Json::Value runCfgData;
          reader.parse(run, runCfgData);

          this->declare_parameter<std::string>("devNAME", "radar");
          this->declare_parameter<std::string>("devSERV", "control_radar");
          this->declare_parameter<std::string>("devSPUB", "radar_status");
          this->declare_parameter<std::string>("devDPUB", "radar_data");
          this->declare_parameter<std::string>("devLOGG", "radar: ");

          devNAME = this->get_parameter("devNAME").as_string();
          devSERV = this->get_parameter("devSERV").as_string();
          devSPUB = this->get_parameter("devSPUB").as_string();
          devDPUB = this->get_parameter("devDPUB").as_string();
          devLOGG = this->get_parameter("devLOGG").as_string();
        
          // calculate parameters
          int numChirps = devCfgData["frameCfg"]["numChirps"].asInt();
          int numSamples = devCfgData["profileCfg"]["numAdcSamples"].asInt();
          int bytesPerSample = 2; // adc either returns 12,14 or 16bit data which all have to be stored over 2 bytes 
          int realOrComplex = (devCfgData["adcbufCfg"]["adcOutputFmt"].asInt()+2) % 3; //if 0 it is complex so 2%3 = 2, if 1 it is real 3%3=1
          int numReceivers = maskToNum(devCfgData["channelCfg"]["rxChannelEn"].asInt()); // convert number to bit mask string with bin() and remove 0b from start of string
          int numTransmitters = devCfgData["frameCfg"]["chirpEndIndex"].asInt() - devCfgData["frameCfg"]["chirpStartIndex"].asInt() + 1;
          
          frameSize = numChirps*numSamples*bytesPerSample*realOrComplex*numReceivers*numTransmitters; // calculate required buffer Size
          
          RCLCPP_INFO(this->get_logger(),"Frame size is: %s" , std::to_string(frameSize).c_str());

          dataToPublish = new unsigned char [frameSize];
          memset(dataToPublish,0x00,frameSize);

          // Create buffer
          RCLCPP_INFO(this->get_logger(),"Created %s byte ring buffer for data capture.\n" , std::to_string(bufSize).c_str());
          bufSize = frameSize*6;
          dataBuf = new unsigned char[bufSize];
          memset( dataBuf, 0, bufSize );
          _readPtr = 0;
          _writePtr = 0;
          _writeBytesAvail = bufSize;
        }

        // Setup ROS2 Components ---------------------------------------------------------------
        RCLCPP_INFO(this->get_logger(),"PUBLISHER:");
        data_publisher = this->create_publisher<dca1000_ros2_pkg::msg::Frame>(devDPUB, 10);
        RCLCPP_INFO(this->get_logger(),"Device publishder started.");
        RCLCPP_INFO(this->get_logger(),"Node Setup Finished.\n");

        RCLCPP_INFO(this->get_logger(),"DATA CAPTURE THREAD:");
        RCLCPP_INFO(this->get_logger(),"Starting data capture daemon.");
        std::thread thr1(&MMWaveDataNode::publish_data_thread, this);
        thr1.detach();
        RCLCPP_INFO(this->get_logger(),"Daemon is running.\n");
    }

  private:

    std::string devNAME;
    std::string devSERV;
    std::string devSPUB;
    std::string devDPUB;
    std::string devLOGG;

    int collect_data(){
        //Receive an incoming message
        clientlen = sizeof(clientaddr);
        bzero(incoming_udp_packet, BUFSIZE); // resets buffer
        if (!softwareTest){
          n = recvfrom(sockfd, incoming_udp_packet, BUFSIZE, 0,
		      (struct sockaddr *) &clientaddr, &clientlen);
        } else {
          n = BUFSIZE;
          unsigned char packet[MAX_PACKET_DATA_SIZE +10] = {0x00};
          packetCount++;
          for (int i =0; i < 4 ; i++){
            packet[i] = (packetCount & (0x000000ff << i*8)) >> i*8;
          }
          memcpy(incoming_udp_packet,packet,sizeof(incoming_udp_packet));
        }
        if (n < 0){
          RCLCPP_INFO(this->get_logger(),"Waiting for data...");
          // Read config data ---------------------------------------------------------------------
          {
            // get jsons
            Json::Reader reader;

            std::string devCfgPath =this->get_parameter("dev_cfg_file_path").get_parameter_value().get<std::string>();
            std::ifstream dev(devCfgPath);
            Json::Value devCfgData;
            reader.parse(dev, devCfgData);

            std::string runCfgPath =this->get_parameter("run_cfg_file_path").get_parameter_value().get<std::string>();
            std::ifstream run(runCfgPath);
            Json::Value runCfgData;
            reader.parse(run, runCfgData);

            // calculate parameters
            int numChirps = devCfgData["frameCfg"]["numChirps"].asInt();
            int numSamples = devCfgData["profileCfg"]["numAdcSamples"].asInt();
            int bytesPerSample = 2; // adc either returns 12,14 or 16bit data which all have to be stored over 2 bytes 
            int realOrComplex = (devCfgData["adcbufCfg"]["adcOutputFmt"].asInt()+2) % 3; //if 0 it is complex so 2%3 = 2, if 1 it is real 3%3=1
            int numReceivers = maskToNum(devCfgData["channelCfg"]["rxChannelEn"].asInt()); // convert number to bit mask string with bin() and remove 0b from start of string
            int numTransmitters = devCfgData["frameCfg"]["chirpEndIndex"].asInt() - devCfgData["frameCfg"]["chirpStartIndex"].asInt() + 1;
            
            frameSize = numChirps*numSamples*bytesPerSample*realOrComplex*numReceivers*numTransmitters; // calculate required buffer Size
            
            dataToPublish = new unsigned char [frameSize];
            memset(dataToPublish,0x00,frameSize);

            // Create buffer
            bufSize = frameSize*6;
            dataBuf = new unsigned char[bufSize];
            memset( dataBuf, 0, bufSize );
            _readPtr = 0;
            _writePtr = 0;
            _writeBytesAvail = bufSize;
          }
        } else {
          //RCLCPP_INFO(this->get_logger(),"Received %s bytes." , std::to_string(n).c_str());
          // get packet number
          prevPackNum = packetNum; 
          packetNum = 0;
          for (int i = 0; i < 4 ;i++){
            packetNum = packetNum | (incoming_udp_packet[i] << i*8);
          }
          //RCLCPP_INFO(this->get_logger(),"Received packet number %s.", std::to_string((packetNum)).c_str());

          // Check for dropped packets and push zeros to buffer
          if ((packetNum- prevPackNum)>1){
            RCLCPP_WARN(this->get_logger(),"Dropped %s packets.", std::to_string((packetNum - prevPackNum)).c_str());
            
            int numZeroPackets = (packetNum - prevPackNum); // calculate the number of missing bytes
            unsigned char zeroBytes[MAX_PACKET_DATA_SIZE] = {0x00}; 
            for(int i = 0; i<numZeroPackets;i++)
            {
              //frameBuf.Write(zeroBytes,MAX_PACKET_DATA_SIZE);
              bufWrite(zeroBytes,MAX_PACKET_DATA_SIZE);
              bytesWritten += MAX_PACKET_DATA_SIZE;
            } 
          } 

          // Push raw data to buffer
          // ISSUE HERE
          //RCLCPP_INFO(this->get_logger(),"Captured %s bytes.", std::to_string((bytesWritten + n - 10)).c_str());
          //frameBuf.Write(incoming_udp_packet+10,n-10); // Write the packet minus first 10 bytes to buffer
          bufWrite(incoming_udp_packet+10,n-10);
          bytesWritten += n-10;
          //RCLCPP_INFO(this->get_logger(),"Pushed %s Bytes to buffer.", std::to_string((n-10)).c_str());
        }

        return 0;
    }

    int bufWrite( unsigned char *dataPtr, int numBytes ) {
      // Simultaneously keep track of how many bytes we've written and our position in the incoming buffer
      if(numBytes > bufSize - _writePtr)
      {		//std::cout<<"TRACE 5"<<std::endl;
            int len = bufSize-_writePtr;
            memcpy(dataBuf+_writePtr,dataPtr,len);
            memcpy(dataBuf, dataPtr+len, numBytes-len);
      }
      else
      {		
          memcpy(dataBuf+_writePtr, dataPtr, numBytes);
      }

      _writePtr = (_writePtr + numBytes) % bufSize;
      _writeBytesAvail -= numBytes;

      return numBytes;
    }

    int bufRead( unsigned char *dataPtr, int numBytes ) {
      if(numBytes > bufSize - _readPtr)
      {
            int len = bufSize-_readPtr;
            memcpy(dataPtr,dataBuf+_readPtr,len);
            memcpy(dataPtr+len, dataBuf, numBytes-len);
      }
      else
      {
            memcpy(dataPtr, dataBuf+_readPtr, numBytes);
      }

      _readPtr = (_readPtr + numBytes) % bufSize;
      _writeBytesAvail += numBytes;

      return numBytes;
    }

    // %---------------------------------------------------------------------------------------------------------
    void publish_data_thread()
    {
      RCLCPP_INFO(this->get_logger(),"DATA COLLECTION:");
      for(;;){ publish_data(); }    
    }


    void publish_data()
    {
      collect_data();
      // auto message = radar_interfaces::msg::Frame();
      auto message = dca1000_ros2_pkg::msg::Frame();

      if (bytesWritten >= frameSize){
        bufRead(dataToPublish,frameSize);
        bytesWritten -= frameSize;
        std::vector<unsigned char> data_vector(dataToPublish, dataToPublish + frameSize);
        message.frame_data = data_vector;
        message.frame_size = frameSize;
        message.header.stamp = this->get_clock()->now();
        message.header.set__frame_id(std::to_string(count));
        count++;
        RCLCPP_INFO(this->get_logger(), "Publishing Frame %s.", std::to_string(count).c_str());
        data_publisher->publish(message);
        //RCLCPP_INFO(this->get_logger(), "Published Frame.\n");
      }
    }

    int maskToNum(long n) {
      long i;
      int num = n;
      int sum = 0;

      for (i = 0; i <4 ; i++)
      {
        sum += num%2;
        num = num/2;
      }
      return sum;
    }

    // ROS2
    rclcpp::TimerBase::SharedPtr timer_;
    // rclcpp::Publisher<radar_interfaces::msg::Frame>::SharedPtr data_publisher;
    rclcpp::Publisher<dca1000_ros2_pkg::msg::Frame>::SharedPtr data_publisher;

    int count;
    const bool softwareTest = false;
    int packetCount = 0;

    //Threading 
    std::thread thr1;

    // Buffer
    int frameSize;
    unsigned char * dataToPublish;
    unsigned char * dataBuf;
    int _readPtr;
    int _writePtr;
    int _writeBytesAvail;
    int bufSize;
    RingBuffer frameBuf;
    

    // Data Collection Variables
    int packetNum = 0;
    int prevPackNum;
    int bytesWritten = 0;

    // Socket Variables
    int sockfd; /* Socket file descriptor number */
    socklen_t clientlen; /* byte size of client's address */
    struct sockaddr_in serveraddr; /* server's address */
    struct sockaddr_in clientaddr; /* clients addréss */
    struct hostent *hostp; /* client host info */
    unsigned char incoming_udp_packet[BUFSIZE]; /* Buffer for incoming packets*/
    char *hostaddrp; /* dotted decimal host addr string */
    int optval; /* flag value for setsockopt */
    int n; /* message byte size */

};

void signal_callback_handler(int signum) {
   std::cout << "Ending data collection." <<  std::endl;
   exit(signum);
}

int main(int argc, char * argv[])
{
  signal(SIGINT, signal_callback_handler);
  rclcpp::init(argc, argv);

  rclcpp::Node::SharedPtr node = std::make_shared<MMWaveDataNode>();
  rclcpp::executors::MultiThreadedExecutor executor;
  executor.add_node(node);
  executor.spin();
  rclcpp::shutdown();
  return EXIT_SUCCESS;
}
