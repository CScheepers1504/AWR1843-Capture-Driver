// generated from rosidl_typesupport_introspection_c/resource/idl__type_support.c.em
// with input from dca1000_ros2_pkg:msg/ControlStatus.idl
// generated code does not contain a copyright notice

#include <stddef.h>
#include "dca1000_ros2_pkg/msg/detail/control_status__rosidl_typesupport_introspection_c.h"
#include "dca1000_ros2_pkg/msg/rosidl_typesupport_introspection_c__visibility_control.h"
#include "rosidl_typesupport_introspection_c/field_types.h"
#include "rosidl_typesupport_introspection_c/identifier.h"
#include "rosidl_typesupport_introspection_c/message_introspection.h"
#include "dca1000_ros2_pkg/msg/detail/control_status__functions.h"
#include "dca1000_ros2_pkg/msg/detail/control_status__struct.h"


// Include directives for member types
// Member `header`
#include "std_msgs/msg/header.h"
// Member `header`
#include "std_msgs/msg/detail/header__rosidl_typesupport_introspection_c.h"
// Member `dev_name`
#include "rosidl_runtime_c/string_functions.h"

#ifdef __cplusplus
extern "C"
{
#endif

void ControlStatus__rosidl_typesupport_introspection_c__ControlStatus_init_function(
  void * message_memory, enum rosidl_runtime_c__message_initialization _init)
{
  // TODO(karsten1987): initializers are not yet implemented for typesupport c
  // see https://github.com/ros2/ros2/issues/397
  (void) _init;
  dca1000_ros2_pkg__msg__ControlStatus__init(message_memory);
}

void ControlStatus__rosidl_typesupport_introspection_c__ControlStatus_fini_function(void * message_memory)
{
  dca1000_ros2_pkg__msg__ControlStatus__fini(message_memory);
}

static rosidl_typesupport_introspection_c__MessageMember ControlStatus__rosidl_typesupport_introspection_c__ControlStatus_message_member_array[5] = {
  {
    "header",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    NULL,  // members of sub message (initialized later)
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(dca1000_ros2_pkg__msg__ControlStatus, header),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "dev_name",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_STRING,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(dca1000_ros2_pkg__msg__ControlStatus, dev_name),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "pwron",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_BOOLEAN,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(dca1000_ros2_pkg__msg__ControlStatus, pwron),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "setup",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_BOOLEAN,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(dca1000_ros2_pkg__msg__ControlStatus, setup),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL  // resize(index) function pointer
  },
  {
    "recrd",  // name
    rosidl_typesupport_introspection_c__ROS_TYPE_BOOLEAN,  // type
    0,  // upper bound of string
    NULL,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(dca1000_ros2_pkg__msg__ControlStatus, recrd),  // bytes offset in struct
    NULL,  // default value
    NULL,  // size() function pointer
    NULL,  // get_const(index) function pointer
    NULL,  // get(index) function pointer
    NULL  // resize(index) function pointer
  }
};

static const rosidl_typesupport_introspection_c__MessageMembers ControlStatus__rosidl_typesupport_introspection_c__ControlStatus_message_members = {
  "dca1000_ros2_pkg__msg",  // message namespace
  "ControlStatus",  // message name
  5,  // number of fields
  sizeof(dca1000_ros2_pkg__msg__ControlStatus),
  ControlStatus__rosidl_typesupport_introspection_c__ControlStatus_message_member_array,  // message members
  ControlStatus__rosidl_typesupport_introspection_c__ControlStatus_init_function,  // function to initialize message memory (memory has to be allocated)
  ControlStatus__rosidl_typesupport_introspection_c__ControlStatus_fini_function  // function to terminate message instance (will not free memory)
};

// this is not const since it must be initialized on first access
// since C does not allow non-integral compile-time constants
static rosidl_message_type_support_t ControlStatus__rosidl_typesupport_introspection_c__ControlStatus_message_type_support_handle = {
  0,
  &ControlStatus__rosidl_typesupport_introspection_c__ControlStatus_message_members,
  get_message_typesupport_handle_function,
};

ROSIDL_TYPESUPPORT_INTROSPECTION_C_EXPORT_dca1000_ros2_pkg
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, dca1000_ros2_pkg, msg, ControlStatus)() {
  ControlStatus__rosidl_typesupport_introspection_c__ControlStatus_message_member_array[0].members_ =
    ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_c, std_msgs, msg, Header)();
  if (!ControlStatus__rosidl_typesupport_introspection_c__ControlStatus_message_type_support_handle.typesupport_identifier) {
    ControlStatus__rosidl_typesupport_introspection_c__ControlStatus_message_type_support_handle.typesupport_identifier =
      rosidl_typesupport_introspection_c__identifier;
  }
  return &ControlStatus__rosidl_typesupport_introspection_c__ControlStatus_message_type_support_handle;
}
#ifdef __cplusplus
}
#endif
