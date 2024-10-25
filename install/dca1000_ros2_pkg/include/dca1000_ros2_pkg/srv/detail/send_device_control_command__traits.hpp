// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from dca1000_ros2_pkg:srv/SendDeviceControlCommand.idl
// generated code does not contain a copyright notice

#ifndef DCA1000_ROS2_PKG__SRV__DETAIL__SEND_DEVICE_CONTROL_COMMAND__TRAITS_HPP_
#define DCA1000_ROS2_PKG__SRV__DETAIL__SEND_DEVICE_CONTROL_COMMAND__TRAITS_HPP_

#include "dca1000_ros2_pkg/srv/detail/send_device_control_command__struct.hpp"
#include <rosidl_runtime_cpp/traits.hpp>
#include <stdint.h>
#include <type_traits>

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Request>()
{
  return "dca1000_ros2_pkg::srv::SendDeviceControlCommand_Request";
}

template<>
inline const char * name<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Request>()
{
  return "dca1000_ros2_pkg/srv/SendDeviceControlCommand_Request";
}

template<>
struct has_fixed_size<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Request>
  : std::integral_constant<bool, true> {};

template<>
struct has_bounded_size<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Request>
  : std::integral_constant<bool, true> {};

template<>
struct is_message<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Request>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Response>()
{
  return "dca1000_ros2_pkg::srv::SendDeviceControlCommand_Response";
}

template<>
inline const char * name<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Response>()
{
  return "dca1000_ros2_pkg/srv/SendDeviceControlCommand_Response";
}

template<>
struct has_fixed_size<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Response>
  : std::integral_constant<bool, true> {};

template<>
struct has_bounded_size<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Response>
  : std::integral_constant<bool, true> {};

template<>
struct is_message<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Response>
  : std::true_type {};

}  // namespace rosidl_generator_traits

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<dca1000_ros2_pkg::srv::SendDeviceControlCommand>()
{
  return "dca1000_ros2_pkg::srv::SendDeviceControlCommand";
}

template<>
inline const char * name<dca1000_ros2_pkg::srv::SendDeviceControlCommand>()
{
  return "dca1000_ros2_pkg/srv/SendDeviceControlCommand";
}

template<>
struct has_fixed_size<dca1000_ros2_pkg::srv::SendDeviceControlCommand>
  : std::integral_constant<
    bool,
    has_fixed_size<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Request>::value &&
    has_fixed_size<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Response>::value
  >
{
};

template<>
struct has_bounded_size<dca1000_ros2_pkg::srv::SendDeviceControlCommand>
  : std::integral_constant<
    bool,
    has_bounded_size<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Request>::value &&
    has_bounded_size<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Response>::value
  >
{
};

template<>
struct is_service<dca1000_ros2_pkg::srv::SendDeviceControlCommand>
  : std::true_type
{
};

template<>
struct is_service_request<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Request>
  : std::true_type
{
};

template<>
struct is_service_response<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Response>
  : std::true_type
{
};

}  // namespace rosidl_generator_traits

#endif  // DCA1000_ROS2_PKG__SRV__DETAIL__SEND_DEVICE_CONTROL_COMMAND__TRAITS_HPP_
