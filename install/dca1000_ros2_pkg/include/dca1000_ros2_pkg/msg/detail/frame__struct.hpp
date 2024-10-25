// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from dca1000_ros2_pkg:msg/Frame.idl
// generated code does not contain a copyright notice

#ifndef DCA1000_ROS2_PKG__MSG__DETAIL__FRAME__STRUCT_HPP_
#define DCA1000_ROS2_PKG__MSG__DETAIL__FRAME__STRUCT_HPP_

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
# define DEPRECATED__dca1000_ros2_pkg__msg__Frame __attribute__((deprecated))
#else
# define DEPRECATED__dca1000_ros2_pkg__msg__Frame __declspec(deprecated)
#endif

namespace dca1000_ros2_pkg
{

namespace msg
{

// message struct
template<class ContainerAllocator>
struct Frame_
{
  using Type = Frame_<ContainerAllocator>;

  explicit Frame_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->frame_size = 0ul;
    }
  }

  explicit Frame_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  : header(_alloc, _init)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->frame_size = 0ul;
    }
  }

  // field types and members
  using _header_type =
    std_msgs::msg::Header_<ContainerAllocator>;
  _header_type header;
  using _frame_size_type =
    uint32_t;
  _frame_size_type frame_size;
  using _frame_data_type =
    std::vector<unsigned char, typename ContainerAllocator::template rebind<unsigned char>::other>;
  _frame_data_type frame_data;

  // setters for named parameter idiom
  Type & set__header(
    const std_msgs::msg::Header_<ContainerAllocator> & _arg)
  {
    this->header = _arg;
    return *this;
  }
  Type & set__frame_size(
    const uint32_t & _arg)
  {
    this->frame_size = _arg;
    return *this;
  }
  Type & set__frame_data(
    const std::vector<unsigned char, typename ContainerAllocator::template rebind<unsigned char>::other> & _arg)
  {
    this->frame_data = _arg;
    return *this;
  }

  // constant declarations

  // pointer types
  using RawPtr =
    dca1000_ros2_pkg::msg::Frame_<ContainerAllocator> *;
  using ConstRawPtr =
    const dca1000_ros2_pkg::msg::Frame_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<dca1000_ros2_pkg::msg::Frame_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<dca1000_ros2_pkg::msg::Frame_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      dca1000_ros2_pkg::msg::Frame_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<dca1000_ros2_pkg::msg::Frame_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      dca1000_ros2_pkg::msg::Frame_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<dca1000_ros2_pkg::msg::Frame_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<dca1000_ros2_pkg::msg::Frame_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<dca1000_ros2_pkg::msg::Frame_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__dca1000_ros2_pkg__msg__Frame
    std::shared_ptr<dca1000_ros2_pkg::msg::Frame_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__dca1000_ros2_pkg__msg__Frame
    std::shared_ptr<dca1000_ros2_pkg::msg::Frame_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const Frame_ & other) const
  {
    if (this->header != other.header) {
      return false;
    }
    if (this->frame_size != other.frame_size) {
      return false;
    }
    if (this->frame_data != other.frame_data) {
      return false;
    }
    return true;
  }
  bool operator!=(const Frame_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct Frame_

// alias to use template instance with default allocator
using Frame =
  dca1000_ros2_pkg::msg::Frame_<std::allocator<void>>;

// constant definitions

}  // namespace msg

}  // namespace dca1000_ros2_pkg

#endif  // DCA1000_ROS2_PKG__MSG__DETAIL__FRAME__STRUCT_HPP_
