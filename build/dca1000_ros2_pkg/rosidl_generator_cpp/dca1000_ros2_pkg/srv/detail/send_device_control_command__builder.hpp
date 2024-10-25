// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from dca1000_ros2_pkg:srv/SendDeviceControlCommand.idl
// generated code does not contain a copyright notice

#ifndef DCA1000_ROS2_PKG__SRV__DETAIL__SEND_DEVICE_CONTROL_COMMAND__BUILDER_HPP_
#define DCA1000_ROS2_PKG__SRV__DETAIL__SEND_DEVICE_CONTROL_COMMAND__BUILDER_HPP_

#include "dca1000_ros2_pkg/srv/detail/send_device_control_command__struct.hpp"
#include <rosidl_runtime_cpp/message_initialization.hpp>
#include <algorithm>
#include <utility>


namespace dca1000_ros2_pkg
{

namespace srv
{

namespace builder
{

class Init_SendDeviceControlCommand_Request_command
{
public:
  Init_SendDeviceControlCommand_Request_command()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::dca1000_ros2_pkg::srv::SendDeviceControlCommand_Request command(::dca1000_ros2_pkg::srv::SendDeviceControlCommand_Request::_command_type arg)
  {
    msg_.command = std::move(arg);
    return std::move(msg_);
  }

private:
  ::dca1000_ros2_pkg::srv::SendDeviceControlCommand_Request msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::dca1000_ros2_pkg::srv::SendDeviceControlCommand_Request>()
{
  return dca1000_ros2_pkg::srv::builder::Init_SendDeviceControlCommand_Request_command();
}

}  // namespace dca1000_ros2_pkg


namespace dca1000_ros2_pkg
{

namespace srv
{

namespace builder
{

class Init_SendDeviceControlCommand_Response_status
{
public:
  Init_SendDeviceControlCommand_Response_status()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  ::dca1000_ros2_pkg::srv::SendDeviceControlCommand_Response status(::dca1000_ros2_pkg::srv::SendDeviceControlCommand_Response::_status_type arg)
  {
    msg_.status = std::move(arg);
    return std::move(msg_);
  }

private:
  ::dca1000_ros2_pkg::srv::SendDeviceControlCommand_Response msg_;
};

}  // namespace builder

}  // namespace srv

template<typename MessageType>
auto build();

template<>
inline
auto build<::dca1000_ros2_pkg::srv::SendDeviceControlCommand_Response>()
{
  return dca1000_ros2_pkg::srv::builder::Init_SendDeviceControlCommand_Response_status();
}

}  // namespace dca1000_ros2_pkg

#endif  // DCA1000_ROS2_PKG__SRV__DETAIL__SEND_DEVICE_CONTROL_COMMAND__BUILDER_HPP_
