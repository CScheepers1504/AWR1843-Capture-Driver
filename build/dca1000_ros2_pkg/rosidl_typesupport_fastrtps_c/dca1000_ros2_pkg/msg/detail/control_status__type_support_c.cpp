// generated from rosidl_typesupport_fastrtps_c/resource/idl__type_support_c.cpp.em
// with input from dca1000_ros2_pkg:msg/ControlStatus.idl
// generated code does not contain a copyright notice
#include "dca1000_ros2_pkg/msg/detail/control_status__rosidl_typesupport_fastrtps_c.h"


#include <cassert>
#include <limits>
#include <string>
#include "rosidl_typesupport_fastrtps_c/identifier.h"
#include "rosidl_typesupport_fastrtps_c/wstring_conversion.hpp"
#include "rosidl_typesupport_fastrtps_cpp/message_type_support.h"
#include "dca1000_ros2_pkg/msg/rosidl_typesupport_fastrtps_c__visibility_control.h"
#include "dca1000_ros2_pkg/msg/detail/control_status__struct.h"
#include "dca1000_ros2_pkg/msg/detail/control_status__functions.h"
#include "fastcdr/Cdr.h"

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

// includes and forward declarations of message dependencies and their conversion functions

#if defined(__cplusplus)
extern "C"
{
#endif

#include "rosidl_runtime_c/string.h"  // dev_name
#include "rosidl_runtime_c/string_functions.h"  // dev_name
#include "std_msgs/msg/detail/header__functions.h"  // header

// forward declare type support functions
ROSIDL_TYPESUPPORT_FASTRTPS_C_IMPORT_dca1000_ros2_pkg
size_t get_serialized_size_std_msgs__msg__Header(
  const void * untyped_ros_message,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_IMPORT_dca1000_ros2_pkg
size_t max_serialized_size_std_msgs__msg__Header(
  bool & full_bounded,
  size_t current_alignment);

ROSIDL_TYPESUPPORT_FASTRTPS_C_IMPORT_dca1000_ros2_pkg
const rosidl_message_type_support_t *
  ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, std_msgs, msg, Header)();


using _ControlStatus__ros_msg_type = dca1000_ros2_pkg__msg__ControlStatus;

static bool _ControlStatus__cdr_serialize(
  const void * untyped_ros_message,
  eprosima::fastcdr::Cdr & cdr)
{
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  const _ControlStatus__ros_msg_type * ros_message = static_cast<const _ControlStatus__ros_msg_type *>(untyped_ros_message);
  // Field name: header
  {
    const message_type_support_callbacks_t * callbacks =
      static_cast<const message_type_support_callbacks_t *>(
      ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(
        rosidl_typesupport_fastrtps_c, std_msgs, msg, Header
      )()->data);
    if (!callbacks->cdr_serialize(
        &ros_message->header, cdr))
    {
      return false;
    }
  }

  // Field name: dev_name
  {
    const rosidl_runtime_c__String * str = &ros_message->dev_name;
    if (str->capacity == 0 || str->capacity <= str->size) {
      fprintf(stderr, "string capacity not greater than size\n");
      return false;
    }
    if (str->data[str->size] != '\0') {
      fprintf(stderr, "string not null-terminated\n");
      return false;
    }
    cdr << str->data;
  }

  // Field name: pwron
  {
    cdr << (ros_message->pwron ? true : false);
  }

  // Field name: setup
  {
    cdr << (ros_message->setup ? true : false);
  }

  // Field name: recrd
  {
    cdr << (ros_message->recrd ? true : false);
  }

  return true;
}

static bool _ControlStatus__cdr_deserialize(
  eprosima::fastcdr::Cdr & cdr,
  void * untyped_ros_message)
{
  if (!untyped_ros_message) {
    fprintf(stderr, "ros message handle is null\n");
    return false;
  }
  _ControlStatus__ros_msg_type * ros_message = static_cast<_ControlStatus__ros_msg_type *>(untyped_ros_message);
  // Field name: header
  {
    const message_type_support_callbacks_t * callbacks =
      static_cast<const message_type_support_callbacks_t *>(
      ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(
        rosidl_typesupport_fastrtps_c, std_msgs, msg, Header
      )()->data);
    if (!callbacks->cdr_deserialize(
        cdr, &ros_message->header))
    {
      return false;
    }
  }

  // Field name: dev_name
  {
    std::string tmp;
    cdr >> tmp;
    if (!ros_message->dev_name.data) {
      rosidl_runtime_c__String__init(&ros_message->dev_name);
    }
    bool succeeded = rosidl_runtime_c__String__assign(
      &ros_message->dev_name,
      tmp.c_str());
    if (!succeeded) {
      fprintf(stderr, "failed to assign string into field 'dev_name'\n");
      return false;
    }
  }

  // Field name: pwron
  {
    uint8_t tmp;
    cdr >> tmp;
    ros_message->pwron = tmp ? true : false;
  }

  // Field name: setup
  {
    uint8_t tmp;
    cdr >> tmp;
    ros_message->setup = tmp ? true : false;
  }

  // Field name: recrd
  {
    uint8_t tmp;
    cdr >> tmp;
    ros_message->recrd = tmp ? true : false;
  }

  return true;
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_dca1000_ros2_pkg
size_t get_serialized_size_dca1000_ros2_pkg__msg__ControlStatus(
  const void * untyped_ros_message,
  size_t current_alignment)
{
  const _ControlStatus__ros_msg_type * ros_message = static_cast<const _ControlStatus__ros_msg_type *>(untyped_ros_message);
  (void)ros_message;
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;

  // field.name header

  current_alignment += get_serialized_size_std_msgs__msg__Header(
    &(ros_message->header), current_alignment);
  // field.name dev_name
  current_alignment += padding +
    eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
    (ros_message->dev_name.size + 1);
  // field.name pwron
  {
    size_t item_size = sizeof(ros_message->pwron);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name setup
  {
    size_t item_size = sizeof(ros_message->setup);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }
  // field.name recrd
  {
    size_t item_size = sizeof(ros_message->recrd);
    current_alignment += item_size +
      eprosima::fastcdr::Cdr::alignment(current_alignment, item_size);
  }

  return current_alignment - initial_alignment;
}

static uint32_t _ControlStatus__get_serialized_size(const void * untyped_ros_message)
{
  return static_cast<uint32_t>(
    get_serialized_size_dca1000_ros2_pkg__msg__ControlStatus(
      untyped_ros_message, 0));
}

ROSIDL_TYPESUPPORT_FASTRTPS_C_PUBLIC_dca1000_ros2_pkg
size_t max_serialized_size_dca1000_ros2_pkg__msg__ControlStatus(
  bool & full_bounded,
  size_t current_alignment)
{
  size_t initial_alignment = current_alignment;

  const size_t padding = 4;
  const size_t wchar_size = 4;
  (void)padding;
  (void)wchar_size;
  (void)full_bounded;

  // member: header
  {
    size_t array_size = 1;


    for (size_t index = 0; index < array_size; ++index) {
      current_alignment +=
        max_serialized_size_std_msgs__msg__Header(
        full_bounded, current_alignment);
    }
  }
  // member: dev_name
  {
    size_t array_size = 1;

    full_bounded = false;
    for (size_t index = 0; index < array_size; ++index) {
      current_alignment += padding +
        eprosima::fastcdr::Cdr::alignment(current_alignment, padding) +
        1;
    }
  }
  // member: pwron
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: setup
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }
  // member: recrd
  {
    size_t array_size = 1;

    current_alignment += array_size * sizeof(uint8_t);
  }

  return current_alignment - initial_alignment;
}

static size_t _ControlStatus__max_serialized_size(bool & full_bounded)
{
  return max_serialized_size_dca1000_ros2_pkg__msg__ControlStatus(
    full_bounded, 0);
}


static message_type_support_callbacks_t __callbacks_ControlStatus = {
  "dca1000_ros2_pkg::msg",
  "ControlStatus",
  _ControlStatus__cdr_serialize,
  _ControlStatus__cdr_deserialize,
  _ControlStatus__get_serialized_size,
  _ControlStatus__max_serialized_size
};

static rosidl_message_type_support_t _ControlStatus__type_support = {
  rosidl_typesupport_fastrtps_c__identifier,
  &__callbacks_ControlStatus,
  get_message_typesupport_handle_function,
};

const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_fastrtps_c, dca1000_ros2_pkg, msg, ControlStatus)() {
  return &_ControlStatus__type_support;
}

#if defined(__cplusplus)
}
#endif
