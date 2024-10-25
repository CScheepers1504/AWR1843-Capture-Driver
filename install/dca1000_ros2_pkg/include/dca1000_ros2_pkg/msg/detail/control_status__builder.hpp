// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from dca1000_ros2_pkg:msg/ControlStatus.idl
// generated code does not contain a copyright notice

#ifndef DCA1000_ROS2_PKG__MSG__DETAIL__CONTROL_STATUS__BUILDER_HPP_
#define DCA1000_ROS2_PKG__MSG__DETAIL__CONTROL_STATUS__BUILDER_HPP_

#include "dca1000_ros2_pkg/msg/detail/control_status__struct.hpp"
#include <rosidl_runtime_cpp/message_initialization.hpp>
#include <algorithm>
#include <utility>


namespace dca1000_ros2_pkg
{

namespace msg
{

namespace builder
{

class Init_ControlStatus_recrd
{
public:
  explicit Init_ControlStatus_recrd(::dca1000_ros2_pkg::msg::ControlStatus & msg)
  : msg_(msg)
  {}
  ::dca1000_ros2_pkg::msg::ControlStatus recrd(::dca1000_ros2_pkg::msg::ControlStatus::_recrd_type arg)
  {
    msg_.recrd = std::move(arg);
    return std::move(msg_);
  }

private:
  ::dca1000_ros2_pkg::msg::ControlStatus msg_;
};

class Init_ControlStatus_setup
{
public:
  explicit Init_ControlStatus_setup(::dca1000_ros2_pkg::msg::ControlStatus & msg)
  : msg_(msg)
  {}
  Init_ControlStatus_recrd setup(::dca1000_ros2_pkg::msg::ControlStatus::_setup_type arg)
  {
    msg_.setup = std::move(arg);
    return Init_ControlStatus_recrd(msg_);
  }

private:
  ::dca1000_ros2_pkg::msg::ControlStatus msg_;
};

class Init_ControlStatus_pwron
{
public:
  explicit Init_ControlStatus_pwron(::dca1000_ros2_pkg::msg::ControlStatus & msg)
  : msg_(msg)
  {}
  Init_ControlStatus_setup pwron(::dca1000_ros2_pkg::msg::ControlStatus::_pwron_type arg)
  {
    msg_.pwron = std::move(arg);
    return Init_ControlStatus_setup(msg_);
  }

private:
  ::dca1000_ros2_pkg::msg::ControlStatus msg_;
};

class Init_ControlStatus_dev_name
{
public:
  explicit Init_ControlStatus_dev_name(::dca1000_ros2_pkg::msg::ControlStatus & msg)
  : msg_(msg)
  {}
  Init_ControlStatus_pwron dev_name(::dca1000_ros2_pkg::msg::ControlStatus::_dev_name_type arg)
  {
    msg_.dev_name = std::move(arg);
    return Init_ControlStatus_pwron(msg_);
  }

private:
  ::dca1000_ros2_pkg::msg::ControlStatus msg_;
};

class Init_ControlStatus_header
{
public:
  Init_ControlStatus_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_ControlStatus_dev_name header(::dca1000_ros2_pkg::msg::ControlStatus::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_ControlStatus_dev_name(msg_);
  }

private:
  ::dca1000_ros2_pkg::msg::ControlStatus msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::dca1000_ros2_pkg::msg::ControlStatus>()
{
  return dca1000_ros2_pkg::msg::builder::Init_ControlStatus_header();
}

}  // namespace dca1000_ros2_pkg

#endif  // DCA1000_ROS2_PKG__MSG__DETAIL__CONTROL_STATUS__BUILDER_HPP_
