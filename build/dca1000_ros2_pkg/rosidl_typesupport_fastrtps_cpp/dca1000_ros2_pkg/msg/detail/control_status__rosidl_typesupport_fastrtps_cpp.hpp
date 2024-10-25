// generated from rosidl_typesupport_fastrtps_cpp/resource/idl__rosidl_typesupport_fastrtps_cpp.hpp.em
// with input from dca1000_ros2_pkg:msg/ControlStatus.idl
// generated code does not contain a copyright notice

#ifndef DCA1000_ROS2_PKG__MSG__DETAIL__CONTROL_STATUS__ROSIDL_TYPESUPPORT_FASTRTPS_CPP_HPP_
#define DCA1000_ROS2_PKG__MSG__DETAIL__CONTROL_STATUS__ROSIDL_TYPESUPPORT_FASTRTPS_CPP_HPP_

#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_interface/macros.h"
#include "dca1000_ros2_pkg/msg/rosidl_typesupport_fastrtps_cpp__visibility_control.h"
#include "dca1000_ros2_pkg/msg/detail/control_status__struct.hpp"

#ifndef _WIN32
# pragma GCC diagnostic push
# pragma GCC diagnostic ignored "-Wunused-parameter"
# ifdef __clang__
#  pragma clang diagnostic ignored "-Wdeprecated-register"
#  pragma clang diagnostic ignored "-Wreturn-type-c-linkage"
# endif
#endif
#ifndef _WIN32
# pragma GCC diagnostic pop
#endif

#include "fastcdr/Cdr.h"

namespace dca1000_ros2_pkg
{

namespace msg
{

namespace typesupport_fastrtps_cpp
{

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_dca1000_ros2_pkg
cdr_serialize(
  const dca1000_ros2_pkg::msg::ControlStatus & ros_message,
  eprosima::fastcdr::Cdr & cdr);

bool
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_dca1000_ros2_pkg
cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  dca1000_ros2_pkg::msg::ControlStatus & ros_message);

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_dca1000_ros2_pkg
get_serialized_size(
  const dca1000_ros2_pkg::msg::ControlStatus & ros_message,
  size_t current_alignment);

size_t
ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_dca1000_ros2_pkg
max_serialized_size_ControlStatus(
  bool & full_bounded,
  size_t current_alignment);

}  // namespace typesupport_fastrtps_cpp

}  // namespace msg

}  // namespace dca1000_ros2_pkg

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_FASTRTPS_CPP_PUBLIC_dca1000_ros2_pkg
const rosidl_message_type_support_t *
  ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_cpp, dca1000_ros2_pkg, msg, ControlStatus)();

#ifdef __cplusplus
}
#endif

#endif  // DCA1000_ROS2_PKG__MSG__DETAIL__CONTROL_STATUS__ROSIDL_TYPESUPPORT_FASTRTPS_CPP_HPP_
