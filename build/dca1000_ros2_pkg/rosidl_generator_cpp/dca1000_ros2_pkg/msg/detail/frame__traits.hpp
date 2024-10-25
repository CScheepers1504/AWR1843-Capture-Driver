// generated from rosidl_generator_cpp/resource/idl__traits.hpp.em
// with input from dca1000_ros2_pkg:msg/Frame.idl
// generated code does not contain a copyright notice

#ifndef DCA1000_ROS2_PKG__MSG__DETAIL__FRAME__TRAITS_HPP_
#define DCA1000_ROS2_PKG__MSG__DETAIL__FRAME__TRAITS_HPP_

#include "dca1000_ros2_pkg/msg/detail/frame__struct.hpp"
#include <rosidl_runtime_cpp/traits.hpp>
#include <stdint.h>
#include <type_traits>

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__traits.hpp"

namespace rosidl_generator_traits
{

template<>
inline const char * data_type<dca1000_ros2_pkg::msg::Frame>()
{
  return "dca1000_ros2_pkg::msg::Frame";
}

template<>
inline const char * name<dca1000_ros2_pkg::msg::Frame>()
{
  return "dca1000_ros2_pkg/msg/Frame";
}

template<>
struct has_fixed_size<dca1000_ros2_pkg::msg::Frame>
  : std::integral_constant<bool, false> {};

template<>
struct has_bounded_size<dca1000_ros2_pkg::msg::Frame>
  : std::integral_constant<bool, false> {};

template<>
struct is_message<dca1000_ros2_pkg::msg::Frame>
  : std::true_type {};

}  // namespace rosidl_generator_traits

#endif  // DCA1000_ROS2_PKG__MSG__DETAIL__FRAME__TRAITS_HPP_
