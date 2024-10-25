// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from dca1000_ros2_pkg:msg/ControlStatus.idl
// generated code does not contain a copyright notice

#ifndef DCA1000_ROS2_PKG__MSG__DETAIL__CONTROL_STATUS__STRUCT_H_
#define DCA1000_ROS2_PKG__MSG__DETAIL__CONTROL_STATUS__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.h"
// Member 'dev_name'
#include "rosidl_runtime_c/string.h"

// Struct defined in msg/ControlStatus in the package dca1000_ros2_pkg.
typedef struct dca1000_ros2_pkg__msg__ControlStatus
{
  std_msgs__msg__Header header;
  rosidl_runtime_c__String dev_name;
  bool pwron;
  bool setup;
  bool recrd;
} dca1000_ros2_pkg__msg__ControlStatus;

// Struct for a sequence of dca1000_ros2_pkg__msg__ControlStatus.
typedef struct dca1000_ros2_pkg__msg__ControlStatus__Sequence
{
  dca1000_ros2_pkg__msg__ControlStatus * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} dca1000_ros2_pkg__msg__ControlStatus__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // DCA1000_ROS2_PKG__MSG__DETAIL__CONTROL_STATUS__STRUCT_H_
