// generated from rosidl_typesupport_introspection_cpp/resource/idl__type_support.cpp.em
// with input from dca1000_ros2_pkg:msg/Frame.idl
// generated code does not contain a copyright notice

#include "array"
#include "cstddef"
#include "string"
#include "vector"
#include "rosidl_runtime_c/message_type_support_struct.h"
#include "rosidl_typesupport_cpp/message_type_support.hpp"
#include "rosidl_typesupport_interface/macros.h"
#include "dca1000_ros2_pkg/msg/detail/frame__struct.hpp"
#include "rosidl_typesupport_introspection_cpp/field_types.hpp"
#include "rosidl_typesupport_introspection_cpp/identifier.hpp"
#include "rosidl_typesupport_introspection_cpp/message_introspection.hpp"
#include "rosidl_typesupport_introspection_cpp/message_type_support_decl.hpp"
#include "rosidl_typesupport_introspection_cpp/visibility_control.h"

namespace dca1000_ros2_pkg
{

namespace msg
{

namespace rosidl_typesupport_introspection_cpp
{

void Frame_init_function(
  void * message_memory, rosidl_runtime_cpp::MessageInitialization _init)
{
  new (message_memory) dca1000_ros2_pkg::msg::Frame(_init);
}

void Frame_fini_function(void * message_memory)
{
  auto typed_message = static_cast<dca1000_ros2_pkg::msg::Frame *>(message_memory);
  typed_message->~Frame();
}

size_t size_function__Frame__frame_data(const void * untyped_member)
{
  const auto * member = reinterpret_cast<const std::vector<unsigned char> *>(untyped_member);
  return member->size();
}

const void * get_const_function__Frame__frame_data(const void * untyped_member, size_t index)
{
  const auto & member =
    *reinterpret_cast<const std::vector<unsigned char> *>(untyped_member);
  return &member[index];
}

void * get_function__Frame__frame_data(void * untyped_member, size_t index)
{
  auto & member =
    *reinterpret_cast<std::vector<unsigned char> *>(untyped_member);
  return &member[index];
}

void resize_function__Frame__frame_data(void * untyped_member, size_t size)
{
  auto * member =
    reinterpret_cast<std::vector<unsigned char> *>(untyped_member);
  member->resize(size);
}

static const ::rosidl_typesupport_introspection_cpp::MessageMember Frame_message_member_array[3] = {
  {
    "header",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_MESSAGE,  // type
    0,  // upper bound of string
    ::rosidl_typesupport_introspection_cpp::get_message_type_support_handle<std_msgs::msg::Header>(),  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(dca1000_ros2_pkg::msg::Frame, header),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "frame_size",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_UINT32,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    false,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(dca1000_ros2_pkg::msg::Frame, frame_size),  // bytes offset in struct
    nullptr,  // default value
    nullptr,  // size() function pointer
    nullptr,  // get_const(index) function pointer
    nullptr,  // get(index) function pointer
    nullptr  // resize(index) function pointer
  },
  {
    "frame_data",  // name
    ::rosidl_typesupport_introspection_cpp::ROS_TYPE_OCTET,  // type
    0,  // upper bound of string
    nullptr,  // members of sub message
    true,  // is array
    0,  // array size
    false,  // is upper bound
    offsetof(dca1000_ros2_pkg::msg::Frame, frame_data),  // bytes offset in struct
    nullptr,  // default value
    size_function__Frame__frame_data,  // size() function pointer
    get_const_function__Frame__frame_data,  // get_const(index) function pointer
    get_function__Frame__frame_data,  // get(index) function pointer
    resize_function__Frame__frame_data  // resize(index) function pointer
  }
};

static const ::rosidl_typesupport_introspection_cpp::MessageMembers Frame_message_members = {
  "dca1000_ros2_pkg::msg",  // message namespace
  "Frame",  // message name
  3,  // number of fields
  sizeof(dca1000_ros2_pkg::msg::Frame),
  Frame_message_member_array,  // message members
  Frame_init_function,  // function to initialize message memory (memory has to be allocated)
  Frame_fini_function  // function to terminate message instance (will not free memory)
};

static const rosidl_message_type_support_t Frame_message_type_support_handle = {
  ::rosidl_typesupport_introspection_cpp::typesupport_identifier,
  &Frame_message_members,
  get_message_typesupport_handle_function,
};

}  // namespace rosidl_typesupport_introspection_cpp

}  // namespace msg

}  // namespace dca1000_ros2_pkg


namespace rosidl_typesupport_introspection_cpp
{

template<>
ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
get_message_type_support_handle<dca1000_ros2_pkg::msg::Frame>()
{
  return &::dca1000_ros2_pkg::msg::rosidl_typesupport_introspection_cpp::Frame_message_type_support_handle;
}

}  // namespace rosidl_typesupport_introspection_cpp

#ifdef __cplusplus
extern "C"
{
#endif

ROSIDL_TYPESUPPORT_INTROSPECTION_CPP_PUBLIC
const rosidl_message_type_support_t *
ROSIDL_TYPESUPPORT_INTERFACE__MESSAGE_SYMBOL_NAME(rosidl_typesupport_introspection_cpp, dca1000_ros2_pkg, msg, Frame)() {
  return &::dca1000_ros2_pkg::msg::rosidl_typesupport_introspection_cpp::Frame_message_type_support_handle;
}

#ifdef __cplusplus
}
#endif
