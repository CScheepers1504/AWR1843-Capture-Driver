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
#include "mmwave_drv/msg/frame.hpp"
#include "mmwave_drv/ringbuffer.hpp"

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

          std::string package_name = "mmwave_drv";
          std::string share_directory = ament_index_cpp::get_package_share_directory(package_name);
          std::string dev_cfg_file_path = share_directory + "/config/cfgDev.json";

          this->declare_parameter("dev_cfg_file_path", dev_cfg_file_path);

          Json::Reader reader;
          
          std::string devCfgPath =this->get_parameter("dev_cfg_file_path").get_parameter_value().get<std::string>();
          RCLCPP_INFO(this->get_logger(),"getting dev config at %s\n", devCfgPath.c_str());
          std::ifstream dev(devCfgPath);
          Json::Value devCfgData;
          reader.parse(dev, devCfgData);

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
        // Best-effort, not the default reliable QoS. With reliable + KeepLast(10),
        // a subscriber that falls behind blocks publish() (Fast-DDS blocks up to
        // max_blocking_time, default 100 ms) instead of dropping. That stalls the
        // capture thread, so surplus device frames are lost at the socket layer
        // while the published sequence stays contiguous -- the loss is invisible.
        // Measured effect of that throttle: 333 Hz configured, 76 Hz sustained,
        // with only 3 sequence gaps over 2997 frames (capture 2026-08-24_17-54-30).
        //
        // Best-effort makes any shortfall show up honestly as sequence gaps in
        // recorder.py rather than as a silent reduction in frame rate. The
        // subscriber QoS in recorder.py must match or the topics will not connect.
        auto data_qos = rclcpp::QoS(rclcpp::KeepLast(100)).best_effort();
        data_publisher = this->create_publisher<mmwave_drv::msg::Frame>(devDPUB, data_qos);
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

            // calculate parameters
            int numChirps = devCfgData["frameCfg"]["numChirps"].asInt();
            int numSamples = devCfgData["profileCfg"]["numAdcSamples"].asInt();
            int bytesPerSample = 2; // adc either returns 12,14 or 16bit data which all have to be stored over 2 bytes 
            int realOrComplex = (devCfgData["adcbufCfg"]["adcOutputFmt"].asInt()+2) % 3; //if 0 it is complex so 2%3 = 2, if 1 it is real 3%3=1
            int numReceivers = maskToNum(devCfgData["channelCfg"]["rxChannelEn"].asInt()); // convert number to bit mask string with bin() and remove 0b from start of string
            int numTransmitters = devCfgData["frameCfg"]["chirpEndIndex"].asInt() - devCfgData["frameCfg"]["chirpStartIndex"].asInt() + 1;
            
            frameSize = numChirps*numSamples*bytesPerSample*realOrComplex*numReceivers*numTransmitters; // calculate required buffer Size
            
            // Report what the previous stream left behind, once per idle
            // period (after the first reset both are 0 and this is silent).
            // A nonzero tail is the carry-over that rotates the next take's
            // Tx order if it is not cleared -- and this line appearing at all
            // proves the reset path runs between takes (15 Sep 2026).
            if (bytesWritten != 0 || packetNum != 0) {
              int chirpBytes = numSamples*bytesPerSample*realOrComplex*numReceivers;
              RCLCPP_INFO(this->get_logger(),
                  "Stream idle: resetting capture buffers. Unpublished tail %d B "
                  "(%.2f chirps), last packet number %d.",
                  bytesWritten, (double)bytesWritten / chirpBytes, packetNum);
            }
            // Free the previous run's buffers. This path fires every 2 s while
            // the stream is idle, so without these it leaked both buffers on
            // every timeout.
            delete[] dataToPublish;
            delete[] dataBuf;
            dataToPublish = new unsigned char [frameSize];
            memset(dataToPublish,0x00,frameSize);

            // Create buffer
            bufSize = frameSize*6;
            dataBuf = new unsigned char[bufSize];
            memset( dataBuf, 0, bufSize );
            _readPtr = 0;
            _writePtr = 0;
            _writeBytesAvail = bufSize;
            // bytesWritten counts unread bytes in the ring. It was NOT reset
            // here, so the partial frame left over when the previous take
            // stopped survived into the next take: the pointers restarted at 0
            // but the count still said R bytes were waiting. Every frame of
            // the next take was then published R bytes early, a permanent
            // misalignment. The first take after a launch starts at 0, which
            // is why only takes 2+ on a reused driver went wrong (15 Sep 2026).
            bytesWritten = 0;
            awaitingFirstPacket = true;
            // The DCA1000 restarts its packet counter with the stream, so a
            // stale prevPackNum here would compare against the previous
            // run's numbering.
            prevPackNum = 0;
            packetNum = 0;
            zeroPacketsInserted = 0;
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
          // Once per stream. The dropped-packet check below assumes the
          // DCA1000 restarts its counter at every record start; this line is
          // the evidence for or against that, and n shows the packet size
          // the zero-fill assumes is MAX_PACKET_DATA_SIZE.
          if (awaitingFirstPacket) {
            awaitingFirstPacket = false;
            RCLCPP_INFO(this->get_logger(),
                "Stream started: first packet number %d, %d B, buffered tail %d B.",
                packetNum, n, bytesWritten);
          }

          // Check for dropped packets and push zeros to buffer.
          //
          // The count is (packetNum - prevPackNum - 1), NOT the difference
          // itself: consecutive packets differ by 1 and nothing is missing.
          // Without the -1 every drop inserts one packet too many, which
          // shifts the byte stream permanently and misaligns every frame
          // boundary after the first drop. Downstream that reads as a
          // rotation of the transmitter firing order, because the chirps of
          // a frame are then attributed to the wrong Tx. That is the fault
          // behind the ordering slip observed between 14:28 and 14:30 on
          // 9 September 2026 -- see the session notes for that date.
          if ((packetNum - prevPackNum) > 1){
            int numZeroPackets = packetNum - prevPackNum - 1;
            zeroPacketsInserted += numZeroPackets;
            RCLCPP_WARN(this->get_logger(),
                "Dropped %s packets (%s zero-filled so far this run). Frame "
                "alignment is preserved but these frames carry zeros.",
                std::to_string(numZeroPackets).c_str(),
                std::to_string(zeroPacketsInserted).c_str());
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
      //
      // _writeBytesAvail was maintained but never read, so the ring buffer
      // could lap the reader and overwrite unread bytes with no symptom
      // other than corrupted frames much later. Writing anyway is the right
      // behaviour -- dropping the newest data would be worse -- but it must
      // be visible.
      if(numBytes > _writeBytesAvail){
        RCLCPP_ERROR(this->get_logger(),
            "Ring buffer overflow: writing %s bytes with only %s free of %s. "
            "The reader is not keeping up and frames are now corrupt.",
            std::to_string(numBytes).c_str(),
            std::to_string(_writeBytesAvail).c_str(),
            std::to_string(bufSize).c_str());
      }
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
      auto message = mmwave_drv::msg::Frame();

      if (bytesWritten >= frameSize){
        bufRead(dataToPublish,frameSize);
        bytesWritten -= frameSize;
        std::vector<unsigned char> data_vector(dataToPublish, dataToPublish + frameSize);
        // Move, don't copy. Copy-assignment here duplicated the whole 24 kB frame
        // a second time before DDS serialisation copied it again.
        message.frame_data = std::move(data_vector);
        message.frame_size = frameSize;
        message.header.stamp = this->get_clock()->now();
        message.header.set__frame_id(std::to_string(count));
        count++;
        // Do NOT log per frame here. run.sh pipes stdout through tee, so an
        // RCLCPP_INFO on this path is a synchronous write into a pipe from the
        // capture thread -- at 333 Hz that stalls the thread that should be
        // draining the UDP socket, and surplus device frames are lost in the
        // kernel buffer. Periodic only.
        if (count % 500 == 0){
          RCLCPP_INFO(this->get_logger(), "Published %d frames.", count);
        }
        data_publisher->publish(message);
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
    rclcpp::Publisher<mmwave_drv::msg::Frame>::SharedPtr data_publisher;

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
    // Initialised, and reset alongside the buffer pointers on a config
    // reload. Left indeterminate it feeds the dropped-packet comparison on
    // the very first packet of a run.
    int prevPackNum = 0;
    int bytesWritten = 0;
    // Cumulative zero packets inserted this run. Zero-filling keeps frame
    // alignment but the samples are fabricated, so a capture with a nonzero
    // count here has holes in it and the number belongs in the log.
    long zeroPacketsInserted = 0;
    // True from launch and after every idle reset, until the next packet.
    bool awaitingFirstPacket = true;

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
