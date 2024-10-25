// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from dca1000_ros2_pkg:srv/SendDeviceControlCommand.idl
// generated code does not contain a copyright notice

#ifndef DCA1000_ROS2_PKG__SRV__DETAIL__SEND_DEVICE_CONTROL_COMMAND__STRUCT_H_
#define DCA1000_ROS2_PKG__SRV__DETAIL__SEND_DEVICE_CONTROL_COMMAND__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

/// Constant 'SETUP'.
enum
{
  dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__SETUP = 2
};

/// Constant 'START'.
enum
{
  dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__START = 1
};

/// Constant 'STOP'.
enum
{
  dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__STOP = 0
};

// Struct defined in srv/SendDeviceControlCommand in the package dca1000_ros2_pkg.
typedef struct dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request
{
  int8_t command;
} dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request;

// Struct for a sequence of dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request.
typedef struct dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__Sequence
{
  dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request__Sequence;


// Constants defined in the message

/// Constant 'DONE'.
static const bool dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__DONE = true;

/// Constant 'ERROR'.
static const bool dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__ERROR = false;

// Struct defined in srv/SendDeviceControlCommand in the package dca1000_ros2_pkg.
typedef struct dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response
{
  bool status;
} dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response;

// Struct for a sequence of dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response.
typedef struct dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__Sequence
{
  dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // DCA1000_ROS2_PKG__SRV__DETAIL__SEND_DEVICE_CONTROL_COMMAND__STRUCT_H_
