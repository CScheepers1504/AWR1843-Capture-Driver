// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from dca1000_ros2_pkg:msg/Frame.idl
// generated code does not contain a copyright notice

#ifndef DCA1000_ROS2_PKG__MSG__DETAIL__FRAME__STRUCT_H_
#define DCA1000_ROS2_PKG__MSG__DETAIL__FRAME__STRUCT_H_

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
// Member 'frame_data'
#include "rosidl_runtime_c/primitives_sequence.h"

// Struct defined in msg/Frame in the package dca1000_ros2_pkg.
typedef struct dca1000_ros2_pkg__msg__Frame
{
  std_msgs__msg__Header header;
  uint32_t frame_size;
  rosidl_runtime_c__octet__Sequence frame_data;
} dca1000_ros2_pkg__msg__Frame;

// Struct for a sequence of dca1000_ros2_pkg__msg__Frame.
typedef struct dca1000_ros2_pkg__msg__Frame__Sequence
{
  dca1000_ros2_pkg__msg__Frame * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} dca1000_ros2_pkg__msg__Frame__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // DCA1000_ROS2_PKG__MSG__DETAIL__FRAME__STRUCT_H_
