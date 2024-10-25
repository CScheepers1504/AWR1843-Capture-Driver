// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from dca1000_ros2_pkg:msg/ControlStatus.idl
// generated code does not contain a copyright notice

#ifndef DCA1000_ROS2_PKG__MSG__DETAIL__CONTROL_STATUS__STRUCT_HPP_
#define DCA1000_ROS2_PKG__MSG__DETAIL__CONTROL_STATUS__STRUCT_HPP_

#include <rosidl_runtime_cpp/bounded_vector.hpp>
#include <rosidl_runtime_cpp/message_initialization.hpp>
#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>


// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.hpp"

#ifndef _WIN32
# define DEPRECATED__dca1000_ros2_pkg__msg__ControlStatus __attribute__((deprecated))
#else
# define DEPRECATED__dca1000_ros2_pkg__msg__ControlStatus __declspec(deprecated)
#endif

namespace dca1000_ros2_pkg
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct ControlStatus_
{
  using Type = ControlStatus_<ContainerAllocator>;

  explicit ControlStatus_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->dev_name = "";
      this->pwron = false;
      this->setup = false;
      this->recrd = false;
    }
  }

  explicit ControlStatus_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init),
    dev_name(_alloc)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->dev_name = "";
      this->pwron = false;
      this->setup = false;
      this->recrd = false;
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _dev_name_type =
    std::basic_string<char, std::char_traits<char>, typename ContainerAllocator::template rebind<char>::other>;
  _dev_name_type dev_name;
  using _pwron_type =
    bool;
  _pwron_type pwron;
  using _setup_type =
    bool;
  _setup_type setup;
  using _recrd_type =
    bool;
  _recrd_type recrd;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__dev_name(
    const std::basic_string<char, std::char_traits<char>, typename ContainerAllocator::template rebind<char>::other> & _arg)
  {
    this->dev_name = _arg;
    return *this;
  }
  Type & set__pwron(
    const bool & _arg)
  {
    this->pwron = _arg;
    return *this;
  }
  Type & set__setup(
    const bool & _arg)
  {
    this->setup = _arg;
    return *this;
  }
  Type & set__recrd(
    const bool & _arg)
  {
    this->recrd = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    dca1000_ros2_pkg::msg::ControlStatus_<ContainerAllocator> *;
  using ConstRawPtr =
    const dca1000_ros2_pkg::msg::ControlStatus_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<dca1000_ros2_pkg::msg::ControlStatus_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<dca1000_ros2_pkg::msg::ControlStatus_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      dca1000_ros2_pkg::msg::ControlStatus_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<dca1000_ros2_pkg::msg::ControlStatus_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      dca1000_ros2_pkg::msg::ControlStatus_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<dca1000_ros2_pkg::msg::ControlStatus_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<dca1000_ros2_pkg::msg::ControlStatus_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<dca1000_ros2_pkg::msg::ControlStatus_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__dca1000_ros2_pkg__msg__ControlStatus
    std::shared_ptr<dca1000_ros2_pkg::msg::ControlStatus_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__dca1000_ros2_pkg__msg__ControlStatus
    std::shared_ptr<dca1000_ros2_pkg::msg::ControlStatus_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const ControlStatus_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->dev_name != other.dev_name) {
      return false;
    }
    if (this->pwron != other.pwron) {
      return false;
    }
    if (this->setup != other.setup) {
      return false;
    }
    if (this->recrd != other.recrd) {
      return false;
    }
    return true;
  }
  bool operator!=(const ControlStatus_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct ControlStatus_

// alias to use template instance with default allocator
using ControlStatus =
  dca1000_ros2_pkg::msg::ControlStatus_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace dca1000_ros2_pkg

#endif  // DCA1000_ROS2_PKG__MSG__DETAIL__CONTROL_STATUS__STRUCT_HPP_
