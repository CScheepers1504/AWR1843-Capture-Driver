// generated from rosidl_generator_cpp/resource/idl__struct.hpp.em
// with input from dca1000_ros2_pkg:srv/SendDeviceControlCommand.idl
// generated code does not contain a copyright notice

#ifndef DCA1000_ROS2_PKG__SRV__DETAIL__SEND_DEVICE_CONTROL_COMMAND__STRUCT_HPP_
#define DCA1000_ROS2_PKG__SRV__DETAIL__SEND_DEVICE_CONTROL_COMMAND__STRUCT_HPP_

#include <rosidl_runtime_cpp/bounded_vector.hpp>
#include <rosidl_runtime_cpp/message_initialization.hpp>
#include <algorithm>
#include <array>
#include <memory>
#include <string>
#include <vector>


#ifndef _WIN32
# define DEPRECATED__dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request __attribute__((deprecated))
#else
# define DEPRECATED__dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request __declspec(deprecated)
#endif

namespace dca1000_ros2_pkg
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct SendDeviceControlCommand_Request_
{
  using Type = SendDeviceControlCommand_Request_<ContainerAllocator>;

  explicit SendDeviceControlCommand_Request_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->command = 0;
    }
  }

  explicit SendDeviceControlCommand_Request_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->command = 0;
    }
  }

  // field types and members
  using _command_type =
    int8_t;
  _command_type command;

  // setters for named parameter idiom
  Type & set__command(
    const int8_t & _arg)
  {
    this->command = _arg;
    return *this;
  }

  // constant declarations
  static constexpr int8_t SETUP =
    2;
  static constexpr int8_t START =
    1;
  static constexpr int8_t STOP =
    0;

  // pointer types
  using RawPtr =
    dca1000_ros2_pkg::srv::SendDeviceControlCommand_Request_<ContainerAllocator> *;
  using ConstRawPtr =
    const dca1000_ros2_pkg::srv::SendDeviceControlCommand_Request_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Request_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Request_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      dca1000_ros2_pkg::srv::SendDeviceControlCommand_Request_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Request_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      dca1000_ros2_pkg::srv::SendDeviceControlCommand_Request_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Request_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Request_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Request_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request
    std::shared_ptr<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Request_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__dca1000_ros2_pkg__srv__SendDeviceControlCommand_Request
    std::shared_ptr<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Request_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const SendDeviceControlCommand_Request_ & other) const
  {
    if (this->command != other.command) {
      return false;
    }
    return true;
  }
  bool operator!=(const SendDeviceControlCommand_Request_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct SendDeviceControlCommand_Request_

// alias to use template instance with default allocator
using SendDeviceControlCommand_Request =
  dca1000_ros2_pkg::srv::SendDeviceControlCommand_Request_<std::allocator<void>>;

// constant definitions
template<typename ContainerAllocator>
constexpr int8_t SendDeviceControlCommand_Request_<ContainerAllocator>::SETUP;
template<typename ContainerAllocator>
constexpr int8_t SendDeviceControlCommand_Request_<ContainerAllocator>::START;
template<typename ContainerAllocator>
constexpr int8_t SendDeviceControlCommand_Request_<ContainerAllocator>::STOP;

}  // namespace srv

}  // namespace dca1000_ros2_pkg


#ifndef _WIN32
# define DEPRECATED__dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response __attribute__((deprecated))
#else
# define DEPRECATED__dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response __declspec(deprecated)
#endif

namespace dca1000_ros2_pkg
{

namespace srv
{

// message struct
template<class ContainerAllocator>
struct SendDeviceControlCommand_Response_
{
  using Type = SendDeviceControlCommand_Response_<ContainerAllocator>;

  explicit SendDeviceControlCommand_Response_(rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->status = false;
    }
  }

  explicit SendDeviceControlCommand_Response_(const ContainerAllocator & _alloc, rosidl_runtime_cpp::MessageInitialization _init = rosidl_runtime_cpp::MessageInitialization::ALL)
  {
    (void)_alloc;
    if (rosidl_runtime_cpp::MessageInitialization::ALL == _init ||
      rosidl_runtime_cpp::MessageInitialization::ZERO == _init)
    {
      this->status = false;
    }
  }

  // field types and members
  using _status_type =
    bool;
  _status_type status;

  // setters for named parameter idiom
  Type & set__status(
    const bool & _arg)
  {
    this->status = _arg;
    return *this;
  }

  // constant declarations
  static constexpr bool DONE =
    1;
  // guard against 'ERROR' being predefined by MSVC by temporarily undefining it
#if defined(_WIN32)
#  if defined(ERROR)
#    pragma push_macro("ERROR")
#    undef ERROR
#  endif
#endif
  static constexpr bool ERROR =
    0;
#if defined(_WIN32)
#  pragma warning(suppress : 4602)
#  pragma pop_macro("ERROR")
#endif

  // pointer types
  using RawPtr =
    dca1000_ros2_pkg::srv::SendDeviceControlCommand_Response_<ContainerAllocator> *;
  using ConstRawPtr =
    const dca1000_ros2_pkg::srv::SendDeviceControlCommand_Response_<ContainerAllocator> *;
  using SharedPtr =
    std::shared_ptr<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Response_<ContainerAllocator>>;
  using ConstSharedPtr =
    std::shared_ptr<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Response_<ContainerAllocator> const>;

  template<typename Deleter = std::default_delete<
      dca1000_ros2_pkg::srv::SendDeviceControlCommand_Response_<ContainerAllocator>>>
  using UniquePtrWithDeleter =
    std::unique_ptr<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Response_<ContainerAllocator>, Deleter>;

  using UniquePtr = UniquePtrWithDeleter<>;

  template<typename Deleter = std::default_delete<
      dca1000_ros2_pkg::srv::SendDeviceControlCommand_Response_<ContainerAllocator>>>
  using ConstUniquePtrWithDeleter =
    std::unique_ptr<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Response_<ContainerAllocator> const, Deleter>;
  using ConstUniquePtr = ConstUniquePtrWithDeleter<>;

  using WeakPtr =
    std::weak_ptr<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Response_<ContainerAllocator>>;
  using ConstWeakPtr =
    std::weak_ptr<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Response_<ContainerAllocator> const>;

  // pointer types similar to ROS 1, use SharedPtr / ConstSharedPtr instead
  // NOTE: Can't use 'using' here because GNU C++ can't parse attributes properly
  typedef DEPRECATED__dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response
    std::shared_ptr<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Response_<ContainerAllocator>>
    Ptr;
  typedef DEPRECATED__dca1000_ros2_pkg__srv__SendDeviceControlCommand_Response
    std::shared_ptr<dca1000_ros2_pkg::srv::SendDeviceControlCommand_Response_<ContainerAllocator> const>
    ConstPtr;

  // comparison operators
  bool operator==(const SendDeviceControlCommand_Response_ & other) const
  {
    if (this->status != other.status) {
      return false;
    }
    return true;
  }
  bool operator!=(const SendDeviceControlCommand_Response_ & other) const
  {
    return !this->operator==(other);
  }
};  // struct SendDeviceControlCommand_Response_

// alias to use template instance with default allocator
using SendDeviceControlCommand_Response =
  dca1000_ros2_pkg::srv::SendDeviceControlCommand_Response_<std::allocator<void>>;

// constant definitions
template<typename ContainerAllocator>
constexpr bool SendDeviceControlCommand_Response_<ContainerAllocator>::DONE;
// guard against 'ERROR' being predefined by MSVC by temporarily undefining it
#if defined(_WIN32)
#  if defined(ERROR)
#    pragma push_macro("ERROR")
#    undef ERROR
#  endif
#endif
template<typename ContainerAllocator>
constexpr bool SendDeviceControlCommand_Response_<ContainerAllocator>::ERROR;
#if defined(_WIN32)
#  pragma warning(suppress : 4602)
#  pragma pop_macro("ERROR")
#endif

}  // namespace srv

}  // namespace dca1000_ros2_pkg

namespace dca1000_ros2_pkg
{

namespace srv
{

struct SendDeviceControlCommand
{
  using Request = dca1000_ros2_pkg::srv::SendDeviceControlCommand_Request;
  using Response = dca1000_ros2_pkg::srv::SendDeviceControlCommand_Response;
};

}  // namespace srv

}  // namespace dca1000_ros2_pkg

#endif  // DCA1000_ROS2_PKG__SRV__DETAIL__SEND_DEVICE_CONTROL_COMMAND__STRUCT_HPP_
