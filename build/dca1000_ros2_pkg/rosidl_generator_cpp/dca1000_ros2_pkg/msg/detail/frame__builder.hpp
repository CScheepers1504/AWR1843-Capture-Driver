// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from dca1000_ros2_pkg:msg/Frame.idl
// generated code does not contain a copyright notice

#ifndef DCA1000_ROS2_PKG__MSG__DETAIL__FRAME__BUILDER_HPP_
#define DCA1000_ROS2_PKG__MSG__DETAIL__FRAME__BUILDER_HPP_

#include "dca1000_ros2_pkg/msg/detail/frame__struct.hpp"
#include <rosidl_runtime_cpp/message_initialization.hpp>
#include <algorithm>
#include <utility>


namespace dca1000_ros2_pkg
{

namespace msg
{

namespace builder
{

class Init_Frame_frame_data
{
public:
  explicit Init_Frame_frame_data(::dca1000_ros2_pkg::msg::Frame & msg)
  : msg_(msg)
  {}
  ::dca1000_ros2_pkg::msg::Frame frame_data(::dca1000_ros2_pkg::msg::Frame::_frame_data_type arg)
  {
    msg_.frame_data = std::move(arg);
    return std::move(msg_);
  }

private:
  ::dca1000_ros2_pkg::msg::Frame msg_;
};

class Init_Frame_frame_size
{
public:
  explicit Init_Frame_frame_size(::dca1000_ros2_pkg::msg::Frame & msg)
  : msg_(msg)
  {}
  Init_Frame_frame_data frame_size(::dca1000_ros2_pkg::msg::Frame::_frame_size_type arg)
  {
    msg_.frame_size = std::move(arg);
    return Init_Frame_frame_data(msg_);
  }

private:
  ::dca1000_ros2_pkg::msg::Frame msg_;
};

class Init_Frame_header
{
public:
  Init_Frame_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_Frame_frame_size header(::dca1000_ros2_pkg::msg::Frame::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_Frame_frame_size(msg_);
  }

private:
  ::dca1000_ros2_pkg::msg::Frame msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::dca1000_ros2_pkg::msg::Frame>()
{
  return dca1000_ros2_pkg::msg::builder::Init_Frame_header();
}

}  // namespace dca1000_ros2_pkg

#endif  // DCA1000_ROS2_PKG__MSG__DETAIL__FRAME__BUILDER_HPP_
