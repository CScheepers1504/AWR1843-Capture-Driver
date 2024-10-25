// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from dca1000_ros2_pkg:msg/Frame.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "dca1000_ros2_pkg/msg/detail/frame__rosidl_typesupport_introspection_c.h"
#include "dca1000_ros2_pkg/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "dca1000_ros2_pkg/msg/detail/frame__functions.h"
#include "dca1000_ros2_pkg/msg/detail/frame__struct.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/header.h"
// Member `header`
#include "std_msgs/msg/detail/header__rosidl_typesupport_introspection_c.h"
// Member `frame_data`
#include "rosidl_runtime_c/primitives_sequence_functions.h"

#ifdef __cplusplus
extern "C"
{
#endif

void Frame__rosidl_typesupport_introspection_c__Frame_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  dca1000_ros2_pkg__msg__Frame__init(message_memory);
}

void Frame__rosidl_typesupport_introspection_c__Frame_fini_function(void * message_memory)
{
  dca1000_ros2_pkg__msg__Frame__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember Frame__rosidl_typesupport_introspection_c__Frame_message_member_array[3] = {
  {
    "header",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(dca1000_ros2_pkg__msg__Frame, header),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "frame_size",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_UINT32,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(dca1000_ros2_pkg__msg__Frame, frame_size),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "frame_data",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_OCTET,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(dca1000_ros2_pkg__msg__Frame, frame_data),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers Frame__rosidl_typesupport_introspection_c__Frame_message_members = {
  "dca1000_ros2_pkg__msg",  // message namespace
  "Frame",  // message name
  3,  // number of fields
  sizeof(dca1000_ros2_pkg__msg__Frame),
  Frame__rosidl_typesupport_introspection_c__Frame_message_member_array,  // message members
  Frame__rosidl_typesupport_introspection_c__Frame_init_function,  // function to initialize message memory (memory has to be allocated)
  Frame__rosidl_typesupport_introspection_c__Frame_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t Frame__rosidl_typesupport_introspection_c__Frame_message_type_support_handle = {
  0,
  &Frame__rosidl_typesupport_introspection_c__Frame_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_dca1000_ros2_pkg
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, dca1000_ros2_pkg, msg, Frame)() {
  Frame__rosidl_typesupport_introspection_c__Frame_message_member_array[0].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, std_msgs, msg, Header)();
  if (!Frame__rosidl_typesupport_introspection_c__Frame_message_type_support_handle.typesupport_identifier) {
    Frame__rosidl_typesupport_introspection_c__Frame_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &Frame__rosidl_typesupport_introspection_c__Frame_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
